# Publishing a release

The VERSION and VERSION.json values must agree. A main-branch commit whose message begins with `Release v` explicitly requests publication after the complete ZIP passes every OS job. Ordinary main commits only test. Manual workflow_dispatch with publish=true remains available. A release commit should include its semantic version, for example `Release v0.9.6: simplify startup and comparison setup`.

The publishing job refuses to overwrite an existing tag/release. It uploads the exact tested ZIPs and checksums and then rebuilds the read-only demo from that ZIP. Previous releases and assets are retained. Verify the resulting release, asset digests, OS job reports and demo after publication.
