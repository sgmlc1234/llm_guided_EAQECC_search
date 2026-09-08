# Pending Magma re-run

`eaqecc_data.m` here is a fresh export of every witness in this artifact
(q = 2, 3, 4, 5) plus the instantiated family members: 147 records. The
archived run in the parent directory (122 records, 0 mismatches) predates
this layout and did not include the 27 q = 3 witnesses.

To refresh the corroboration, on a machine with Magma:

    magma -b artifacts/magma/pending/eaqecc_data.m scripts/verify_eaqecc.magma \
        > artifacts/magma/pending/magma_verification.log
    magma -b -e 'print GetVersion();' > artifacts/magma/pending/magma_version.txt   # or record it by hand

then move the three files up into `artifacts/magma/`, delete this
directory, and run `python3 scripts/make_manifest.py`. The auditor's
`magma-crosscheck` reads the record count from the data file, so nothing
else changes.
