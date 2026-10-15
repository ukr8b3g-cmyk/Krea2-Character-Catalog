# Krea2 Character Catalog v0.9.5

For Windows, macOS, and Linux. Python 3.10+ is required. This version focuses on opening the catalog without guessing which file to use.

- Extract the entire catalog ZIP and open the START_HERE file with your OS in its name.
- The root contains three OS-labelled startup files, two README files, a separate AnimaDex-Comparison folder, and one app folder. Internal implementation files are out of the way.
- Use Add image and Edit inside the catalog. Stop server ends the background server and preserves saved data.
- Optional AnimaDex comparison remains separate. Set it up using the bundled folder-selection screen or the optional skill; then open the START_COMPARISON file for your OS in the comparison folder. Use Stop comparison in its own window to end that server.
- Windows startup skips stale PATH entries for drives or folders that no longer exist.

The accepted images, original tags, prompt metadata, and selection decisions are unchanged: 3,809 characters and 110 styles. Rejected-workflow recipes remain a separate ZIP.

Publication is gated on successful finished-ZIP tests on Windows, macOS, and Linux, including the comparison setup launcher, on-screen folder selection, paired image display, and settings persistence using fictitious data. The exact validation run is linked below. Physical macOS/Linux desktop behavior and real AnimaDex cross-OS migration remain unverified. Synthetic tests do not establish character accuracy or real AnimaDex installation compatibility.

Prepare AnimaDex once using its [official installation](https://github.com/zetaneko/AnimaDex) and [dataset import](https://github.com/zetaneko/AnimaDex/blob/main/docs/import-from-site.md) instructions. Download the reference DB and images locally. AnimaDex does not need to stay running for comparison. [Older releases and downloads remain available](https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases).
