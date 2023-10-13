# exif_notes_writer
Takes the JSON export from the Exif Notes app and generates exiftool commands

Requires the [Exif Notes](https://play.google.com/store/apps/details?id=com.tommihirvonen.exifnotes&pcampaignid=web_share) app, available on the Google Play Store for Android.

1. Scan your photos
2. name them such that the end of the filename matches `*_##.tif` where # is a decimal digit. This number should match the count field in Exif Notes.
2. Export your roll as JSON, place the file in the same folder as the scans.
3. Running `python exif_write.py your_export.json` will write the exiftool commands to stdout, you can write this to a .sh file or pipe it to bash directly.
