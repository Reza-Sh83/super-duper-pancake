"""Fixed extent primitives from the reviewed scratch guard at ef66fe7."""

import ctypes
import os
import platform


def preallocate(path,limit):
    """Allocate the complete writable range while preserving logical contents."""
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        lib=ctypes.CDLL(None,use_errno=True)
        if lib.fallocate(fd,1,ctypes.c_longlong(0),ctypes.c_longlong(limit)):
            raise OSError(ctypes.get_errno(),'KEEP_SIZE preallocation unavailable')
        os.fsync(fd)
        value=os.fstat(fd)
        if value.st_size>limit or value.st_blocks*512!=limit:
            raise ValueError('filesystem did not provide exact reserved extent charge')
    finally: os.close(fd)



def protect_extents():
    """No deallocation or O_TRUNC can invalidate the fully allocated ranges."""
    if platform.machine()!='x86_64': raise RuntimeError('unsupported syscall architecture')
    filters=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(6,0,0,0x80000000),
             (0x20,0,0,0),(0x35,0,1,0x40000000),(6,0,0,0x50001)]
    for nr in (76,77,85,285,319,425,426,427,437):
        filters.extend(((0x15,0,1,nr),(6,0,0,0x50001)))
    for nr,offset in ((2,24),(257,32)):
        filters.extend(((0x15,0,4,nr),(0x20,0,0,offset),
                        (0x45,0,1,os.O_TRUNC),(6,0,0,0x50001),(6,0,0,0x7fff0000)))
    filters.append((6,0,0,0x7fff0000))
    class Filter(ctypes.Structure):
        _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
    data=(Filter*len(filters))(*(Filter(*row) for row in filters)); program=Program(len(data),data)
    lib=ctypes.CDLL(None,use_errno=True)
    if lib.prctl(38,1,0,0,0) or lib.prctl(22,2,ctypes.byref(program),0,0):
        raise OSError(ctypes.get_errno(),'extent protection unavailable')
