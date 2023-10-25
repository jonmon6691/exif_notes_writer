#! /usr/bin/env python3
""" exif_write.py - Modifies film scans with exif data from the Exif Notes app """

import json
import argparse
import pathlib
import datetime

# Common component of the command to call for each image
cmd_base = "exiftool -m "

parser = argparse.ArgumentParser(
	description='Generates exiftool commands given a json export of the Exif Notes app. Images to modify are assumed to be in the same folder as the json file. Their names should be of the format rXXX_NN.tif, where XXX is the roll number, and NN is the frame number matching the count field in the exif notes app.')
parser.add_argument('path', metavar='PATH', help='The json file to process. Should be stored in the same folder as the scans.')

args = parser.parse_args()

def dms(decimal_coord):
    "Convert decimal GPS coordinate to Degrees-Minutes-Seconds"
    m,s = divmod(abs(decimal_coord)*3600, 60)
    d,m = divmod(m, 60)
    dms_str = f"{int(d)} {int(m)} {s:0.3f}"
    positive = decimal_coord > 0
    return dms_str, positive

# Read the JSON file
data = None
try:
    with open(args.path, "r") as f:
        data = json.load(f)
except FileNotFoundError as e:
    print("#", e)
    exit(1)
except json.decoder.JSONDecodeError as e:
    print(f"# Error reading '{args.path}', please check the formatting or re-export from Exif Notes")
    print("#", e)
    exit(1)

print(f'# Finished reading \'{args.path}\', found {len(data["frames"])} frame notes.')

# Get a list of images to process
folder = pathlib.Path(args.path).parent.absolute()
images = sorted(list(folder.glob("*_[0-9][0-9].tif")))
image_list = sorted([(int(image.stem[-2:]), image) for image in images], key=lambda x:x[0])
print(f"# Found {len(images)} images in the same folder.")

# Add info common to all frames to the command base
if "camera" in data:
    if "make" in data["camera"]:
        cmd_base += f'-Make="{data["camera"]["make"]}" '
    if "model" in data["camera"]:
        cmd_base += f'-Model="{data["camera"]["model"]}" '
    if "serialNumber" in data["camera"]:
        cmd_base += f'-SerialNumber="{data["camera"]["serialNumber"]}" '
if "iso" in data:
    cmd_base += f'-ISO="{data["iso"]}" '

# Add film stock info to the image's comment. I wish there were standard exif tags for this...
comment_base = ""
if "filmStock" in data:
    if "make" in data["filmStock"]:
        comment_base += f'{data["filmStock"]["make"]} '
    if "model" in data["filmStock"]:
        comment_base += f'{data["filmStock"]["model"]}'

# Get a dict mapping frame counts to frame data
frame_data = {int(frame["count"]): frame for frame in data["frames"]}

last_matching_frame = None
# Loop through all the images, building the command and then printing it
for i, image in image_list:
    frame = None
    # Try to get the matching frame data, if you don't have it, use the most recent
    if i in frame_data:
        frame = frame_data[i]
        last_matching_frame = frame.copy()
        last_matching_frame.pop("shutter",  None)
        last_matching_frame.pop("aperture", None)
    else:
        frame = last_matching_frame

    if frame is None:
        print(f'# Error: Image {image.name} doesn\'t have a corresponding json entry!')
        exit(1)

    # Non-zero indicates that we're useing non-matching frame data, used to increment the timestamp to keep images in order
    offset = i - int(frame["count"])

    # Build off of the common command base
    cmd = cmd_base

    if "lens" in frame:
        if "make" in frame["lens"]:
            cmd += f'-LensMake="{frame["lens"]["make"]}" '

        if "model" in frame["lens"]:
            cmd += f'-LensModel="{frame["lens"]["model"]}" '

        if "make" in frame["lens"] and "model" in frame["lens"]:
            cmd += f'-Lens="{frame["lens"]["make"]} {frame["lens"]["model"]}" '

        if "serialNumber" in frame["lens"]:
            cmd += f'-LensSerialNumber="{frame["lens"]["serialNumber"]}" '
    
    dt = datetime.datetime.fromisoformat(frame["date"]) + datetime.timedelta(minutes=offset)
    dt_string = dt.isoformat(sep=' ', timespec='minutes')
    cmd += f'-DateTime="{dt_string}" -DateTimeOriginal="{dt_string}" '

    if "shutter" in frame:
        shutter_val = frame["shutter"].replace('"','')
        cmd += f'-ShutterSpeedValue="{shutter_val}" -ExposureTime="{shutter_val}" '
    
    if "aperture" in frame:
        cmd += f'-ApertureValue="{frame["aperture"]}" -FNumber="{frame["aperture"]}" '

    if "focalLength" in frame:
        cmd += f'-FocalLength="{frame["focalLength"]}" '

    if "location" in frame and "latitude" in frame["location"] and "longitude" in frame["location"]:
        lat_dms, north = dms(frame["location"]["latitude"])
        lon_dms, east = dms(frame["location"]["longitude"])
        cmd += f'-GPSLatitude="{lat_dms}" -GPSLatitudeRef="{"N" if north else "S"}" -GPSLongitude="{lon_dms}" -GPSLongitudeRef="{"E" if east else "W"}" '

    comment = comment_base
    if "note" in frame and offset == 0:
        comment += ", "+ frame["note"]
    
    if len(comment) > 0:
        cmd += f'-UserComment="{comment}" -ImageDescription="{comment}" '

    cmd += str(image.absolute())
    print(cmd)
