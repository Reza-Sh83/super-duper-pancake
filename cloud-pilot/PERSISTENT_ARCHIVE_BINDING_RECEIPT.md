# Persistent archive content binding

Responds to Architect `b37850d` on the persistent preparation `b1ae1de`. Exact correction **07b565b73d7daf54a3035c4162df34603dc4c80c**. Architect is requested to rerun the focused tests and acknowledge the exact new SHA.

The fresh-process reader now streams the completed tar+xz. It compares sequence, exact relative names, regular non-sparse type, length and SHA-256 of every payload against the sealed source and verified restored inventory. The archive digest in the shutdown seal and all prior replay and read-only preservation checks still apply.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p test_tarxz_persistent.py -v
```

**Three focused tests PASS.** In separate subprocesses, a correctly sealed unrelated archive and a correctly sealed archive with the same member names and sizes but altered payload both failed. A changed archive with an unchanged seal still failed. The valid archive passed, and input inventories were unchanged across all readbacks. The accepted tmpfs runner remains unchanged. Manager retains the persistent backend qualification and dispatch binding.
