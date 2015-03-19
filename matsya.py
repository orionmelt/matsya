# -*- coding: utf-8 -*-

import sys
import re
import json
import cStringIO
import argparse

from PIL import Image
import requests
import numpy


HEADERS = {
    'User-Agent': 'Matsya v0.1 by /u/orionmelt'
}
BASE_PATH = "http://www.reddit.com/static/snoovatar/images/"
DEFAULT_COLOR = (0,255,0)
SNOOVATAR_URL = "http://www.reddit.com/user/%s/snoo"
SNOOVATAR_CONFIG_PATTERN = r"r\.snoovatar\.initSnoovatar\((.*)\)"

# Hex <-> RGB conversion logic from:
# http://stackoverflow.com/questions/214359
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def replace_default_color(image, replacement_color):
    data = numpy.array(image)
    (dr, dg, db) = DEFAULT_COLOR
    (rr, rg, rb) = replacement_color
    red, green, blue = data[:,:,0], data[:,:,1], data[:,:,2]
    mask = (red == dr) & (green == dg) & (blue == db)
    data[:,:,:3][mask] = [rr, rg, rb]
    return Image.fromarray(data)

def render_snoovatar(username, size):
    response = requests.get(SNOOVATAR_URL % username, headers=HEADERS)
    
    if response.status_code == 200:
        m = re.search(SNOOVATAR_CONFIG_PATTERN, response.text, re.MULTILINE)
        if not m and m.groups():
            return None
        config = json.loads(m.groups()[0])
        if not config["public"]:
            return None

        snoovatar = Image.new("RGBA", (800,800), "white")
        
        keys = [
            "body-fill", "body-stroke", "bottoms", "tops", "head-fill", 
            "head-stroke", "glasses", "hats", "grippables", "grippables_left", 
            "grippables_right", "flipped_grippables"
        ]

        for k in keys:
            if not k in config["components"] or not config["components"][k]:
                continue
            
            tailor_url = "%s%s/%s.png" % (
                BASE_PATH, "grippables" if k in [
                    "flipped_grippables", 
                    "grippables_left", 
                    "grippables_right"
                ] else k, config["components"][k]
            )
            tailor_file = cStringIO.StringIO(requests.get(tailor_url).content)
            tailor_image = Image.open(tailor_file)

            snoo_color = hex_to_rgb(config["snoo_color"])
            
            tailor_image = replace_default_color(tailor_image, snoo_color)

            if k in ["flipped_grippables", "grippables_left"]:
                tailor_image = tailor_image.transpose(Image.FLIP_LEFT_RIGHT)

            snoovatar.paste(tailor_image, (0,0), tailor_image)

        snoovatar.thumbnail(size, Image.ANTIALIAS)
        return snoovatar
    else:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument(
        "--size", 
        type=int,
        nargs=2,
        dest="size",
        metavar=("WIDTH", "HEIGHT")
    )
    args = parser.parse_args()
    snoovatar = render_snoovatar(
        args.username, 
        tuple(args.size) if args.size else (100,100)
    )
    if snoovatar:
        snoovatar.save("%s.png" % args.username)
        print "Snoovatar saved: %s.png" % args.username
    else:
        print "No snoovatar found for %s" % args.username

if __name__ == "__main__":
    main()