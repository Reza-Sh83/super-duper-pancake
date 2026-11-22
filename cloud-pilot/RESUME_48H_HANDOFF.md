# 48-hour admission and March input handoff

Capture resumed at 63e3966167376fb5f8cba1491401d6284af9a401. No existing
48-hour job, guarded output or completed launch receipt was found. Manager
2016ee8 holds dispatch and Architect cfdeca0 reports no qualifying clock,
runtime or bounded persistence path. The environment reports no managed
credential binding for an authorized Drive or GCS destination. No launch
or transfer occurred.

## CAPTURE-48-SIZE-01

Read-only sizing under the strict 4.75 GiB intake threshold and separate
256 MiB stop reserve used 635,625,472 retained bytes and a proposed 512 MiB
working envelope. This leaves 3,927,777,279 bytes for retained new archives
over 172,800 seconds, or about 22,730 bytes/s. The repeat archive's observed
average over roughly ten minutes was 16,465 bytes/s. Over 48 hours that
projects to 2.845 GB at 1× and 5.690 GB at 2×. The latter exceeds available
space by 1.763 GB. Both projections are sensitivity scenarios. The floor,
writer headroom and separately enforced concurrent work allowance still
apply. The 30-second local sample gives no sustained cap or backup guarantee.

Manager owns qualification of existing authorized storage, runtime and
clock. The next storage evidence is the original synthetic object's
checksum readback on a distinct executor, once the scoped identity and
private object/version/full digest receipt are present. Then bind and
review finite simultaneous active/sealed segments, compression and restore
work, and a stop rule that halts intake before the cap if upload or readback
lags. A successful upload alone does not authorize archive retirement. Bind
the full plan before Capture can launch once. No new account, permission,
paid service or GCS deployment is authorized.

## MARCH-HANDOFF-01

Capture staged the original 130,559-byte XBTUSD_60.csv member locally as
read-only private evidence. SHA-256 is
`b2c61a3c5c145e7ad24fbfb99a63ea4a3aa2e5653343c1aeaafe0cec5a6692f2`.
Architect adapter 1f3275059d49fd2db3f3746a6d0c368e35bca671 passed its synthetic
test on this executor. Its read-only selector verified the four canonical
digests and exact 26+288 and 26+288 hour partitions. No strategy was scored.
The one executor must be reconciled by Manager: 2016ee8 assigns Implementer,
while Architect wording in cfdeca0 names Architect. Capture owns input
handoff and ran neither role's scoring command.

If the public Kraken archive is reachable from the approved scoring executor,
the exact reproduction needs only the compressed member range. This is a
public source recipe, with no private data or transfer. Project private
output only, and check for an existing member or result before downloading:

- URL: https://assets.kraken.com/marketing/institutions/Kraken_OHLCVT_2026Q1.zip
- Require HTTP 206, ETag `"4fc0e96add0344afa9fe0d0e32ee1af2-63"` and
  Content-Range `bytes 460513412-460567995/523665624`.
- Request that range only, with If-Match and a 54,584-byte response limit.
  Decode the raw DEFLATE payload with wbits=-15 and a 130,560-byte output
  limit. Require exact 130,559 bytes, end-of-stream and the full SHA-256
  above before giving the member to the frozen adapter.
- If the approved executor still receives 403, record that blocker and use
  the retained member only through a verified approved private route.
  Capture found no such cross-executor route in this invocation.

Independent November, registered December and confirmation gates are
untouched. The pilot remains gated.

## Post-publication reconciliation

Manager 8c71761 confirms Implementer as the sole March executor. Implementer
728dddda4692e84b8a314e19a04e9f8fa463648f acquired the exact public member
through bounded ranges, matched Capture's member and all four slice
digests, and completed the frozen comparison once. This supersedes the
March input blocker and the optional reconstruction above. No repeat
acquisition, transfer or scoring is due. Architect independently reviews
the existing result. All validation strategy arms lost money and no
modeled day reached 50%. The full result includes all arms, fees, drawdown,
fills and daily net outcomes.

The 48-hour hold remains. Manager 8c71761 assigns Implementer the next
synthetic rollover/backlog test and Architect the exact review. Use
CAPTURE-48-SIZE-01 as input for a test that refuses a new segment before
exhausting the stop reserve, keeps a sealed segment charged during
compression and verification, refuses retirement on missing or mismatched
durable acknowledgment, and verifies a stopped prefix after replay. The
48-hour projections do not substitute for enforced reservations. Manager
owns unchanged clock, guarded runtime and private storage qualification.
Capture owns one launch only after Manager publishes the reviewed binding.
