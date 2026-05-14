#!/usr/bin/env python3
"""
Convert arcade font from R point data to OTF format via FontForge.
Creates proper rectangular strokes for each line segment.
"""

import re
import sys
import math
from pathlib import Path

# Diacritical marks
DIACRITICS = {
    'dot_above': '39 49 48 38 39',
    'diaeresis': '29 39 38 28 29 :  59 69 68 58 59',
    'acute': '39 59',
    'grave': '59 39',
    'circumflex': '29 49 69',
    'tilde': '29 39 49 59 69',
    'ring': '39 49 48 38 39',
    'cedilla': '40 30 20',
    'ogonek': '70 60 50',
    'caron': '69 49 29',
    'stroke': '14 74',
}

# Extended Latin characters
EXTENDED_LATIN = {
    'Ä': ('A', 'diaeresis', -1), 'ä': ('a', 'diaeresis', -1),
    'Ö': ('O', 'diaeresis', -1), 'ö': ('o', 'diaeresis', -1),
    'Ü': ('U', 'diaeresis', -1), 'ü': ('u', 'diaeresis', -1),
    'ß': ('B', None, 0),
    'Å': ('A', 'ring', -1), 'å': ('a', 'ring', -1),
    'Æ': ('A', None, 0), 'æ': ('a', None, 0),
    'Ø': ('O', 'stroke', 0), 'ø': ('o', 'stroke', 0),
    'À': ('A', 'grave', -1), 'à': ('a', 'grave', -1),
    'Á': ('A', 'acute', -1), 'á': ('a', 'acute', -1),
    'Â': ('A', 'circumflex', -1), 'â': ('a', 'circumflex', -1),
    'É': ('E', 'acute', -1), 'é': ('e', 'acute', -1),
    'È': ('E', 'grave', -1), 'è': ('e', 'grave', -1),
    'Ê': ('E', 'circumflex', -1), 'ê': ('e', 'circumflex', -1),
    'Ë': ('E', 'diaeresis', -1), 'ë': ('e', 'diaeresis', -1),
    'Ï': ('I', 'diaeresis', -1), 'ï': ('i', 'diaeresis', -1),
    'Î': ('I', 'circumflex', -1), 'î': ('i', 'circumflex', -1),
    'Ô': ('O', 'circumflex', -1), 'ô': ('o', 'circumflex', -1),
    'Ù': ('U', 'grave', -1), 'ù': ('u', 'grave', -1),
    'Û': ('U', 'circumflex', -1), 'û': ('u', 'circumflex', -1),
    'Ç': ('C', 'cedilla', 1), 'ç': ('c', 'cedilla', 1),
    'Ñ': ('N', 'tilde', -1), 'ñ': ('n', 'tilde', -1),
    'Ą': ('A', 'ogonek', 1), 'ą': ('a', 'ogonek', 1),
    'Ć': ('C', 'acute', -1), 'ć': ('c', 'acute', -1),
    'Ę': ('E', 'ogonek', 1), 'ę': ('e', 'ogonek', 1),
    'Ł': ('L', 'stroke', 0), 'ł': ('l', 'stroke', 0),
    'Ń': ('N', 'acute', -1), 'ń': ('n', 'acute', -1),
    'Ó': ('O', 'acute', -1), 'ó': ('o', 'acute', -1),
    'Ś': ('S', 'acute', -1), 'ś': ('s', 'acute', -1),
    'Ź': ('Z', 'acute', -1), 'ź': ('z', 'acute', -1),
    'Ż': ('Z', 'dot_above', -1), 'ż': ('z', 'dot_above', -1),
    'Č': ('C', 'caron', -1), 'č': ('c', 'caron', -1),
    'Ď': ('D', 'caron', -1), 'ď': ('d', 'caron', -1),
    'Ě': ('E', 'caron', -1), 'ě': ('e', 'caron', -1),
    'Ň': ('N', 'caron', -1), 'ň': ('n', 'caron', -1),
    'Ř': ('R', 'caron', -1), 'ř': ('r', 'caron', -1),
    'Š': ('S', 'caron', -1), 'š': ('s', 'caron', -1),
    'Ť': ('T', 'caron', -1), 'ť': ('t', 'caron', -1),
    'Ů': ('U', 'ring', -1), 'ů': ('u', 'ring', -1),
    'Ž': ('Z', 'caron', -1), 'ž': ('z', 'caron', -1),
}


def parse_r_font_file(r_file_path):
    """
    Parse the R file to extract the arcode_font_point_sets list.
    Returns a dictionary mapping characters to their point set strings.
    """
    try:
        with open(r_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the arcode_font_point_sets list definition
        # Pattern matches: CHAR = "point_set" or CHAR = 'point_set' or `CHAR` = "point_set"
        pattern = r'`?([^`=\s]+)`?\s*=\s*["\']([^"\']+)["\']'
        
        font_data = {}
        for match in re.finditer(pattern, content):
            char = match.group(1)
            point_set = match.group(2)
            
            # Handle backtick-quoted characters (like `0`, ` `, etc.)
            if len(char) == 1:
                font_data[char] = point_set
        
        # Add lowercase versions for uppercase letters
        uppercase_letters = [c for c in font_data.keys() if c.isupper() and c.isalpha()]
        for letter in uppercase_letters:
            font_data[letter.lower()] = font_data[letter]
        
        return font_data
        
    except FileNotFoundError:
        print(f"ERROR: R file not found: {r_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR parsing R file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def parse_points(points_string):
    points_string = re.sub(r'\s+', '', points_string)
    coords = [int(c) for c in points_string]
    return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]


def parse_strokes(point_set):
    stroke_strings = point_set.split(':')
    return [parse_points(s.strip()) for s in stroke_strings]


def scale_coords(x, y, scale=100, y_offset=0):
    """Scale coordinates WITHOUT flipping Y-axis."""
    scaled_x = x * scale
    # Don't flip - use Y as-is from R data
    scaled_y = y * scale + (y_offset * scale)
    return scaled_x, scaled_y


def create_line_rectangle(x1, y1, x2, y2, width):
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    
    if length < 0.001:
        return []
    
    dx /= length
    dy /= length
    perp_x = -dy
    perp_y = dx
    half_w = width / 2.0
    
    p1 = (x1 + perp_x * half_w, y1 + perp_y * half_w)
    p2 = (x2 + perp_x * half_w, y2 + perp_y * half_w)
    p3 = (x2 - perp_x * half_w, y2 - perp_y * half_w)
    p4 = (x1 - perp_x * half_w, y1 - perp_y * half_w)
    
    return [p1, p2, p3, p4]


def draw_strokes(pen, strokes, stroke_width, y_offset=0):
    for stroke in strokes:
        if len(stroke) < 2:
            continue
        
        scaled_stroke = [scale_coords(x, y, y_offset=y_offset) for x, y in stroke]
        
        for i in range(len(scaled_stroke) - 1):
            x1, y1 = scaled_stroke[i]
            x2, y2 = scaled_stroke[i + 1]
            
            rect = create_line_rectangle(x1, y1, x2, y2, stroke_width)
            
            if len(rect) == 4:
                pen.moveTo(rect[0])
                pen.lineTo(rect[1])
                pen.lineTo(rect[2])
                pen.lineTo(rect[3])
                pen.closePath()


def create_composite_glyph(pen, base_char, diacritic, y_offset, stroke_width, font_data):
    if base_char in font_data:
        base_strokes = parse_strokes(font_data[base_char])
        draw_strokes(pen, base_strokes, stroke_width)
    
    if diacritic and diacritic in DIACRITICS:
        diacritic_strokes = parse_strokes(DIACRITICS[diacritic])
        draw_strokes(pen, diacritic_strokes, stroke_width, y_offset)


def build_font_object(font_data, stroke_width=40):
    """Build and return a FontForge font object with all glyphs."""
    try:
        import fontforge
    except ImportError:
        print("ERROR: FontForge Python module not found.")
        return None
    
    print(f"Building font object...")
    
    font = fontforge.font()
    font.fontname = "ArcadeFont"
    font.fullname = "Arcade Font Extended"
    font.familyname = "Arcade"
    font.weight = "Regular"
    font.copyright = "Generated from R arcade font data"
    font.version = "001.000"
    font.ascent = 800
    font.descent = 200
    font.em = 1000
    
    glyph_count = 0
    
    for char, point_set in font_data.items():
        unicode_val = ord(char)
        glyph = font.createChar(unicode_val)
        glyph.width = 900
        
        strokes = parse_strokes(point_set)
        pen = glyph.glyphPen()
        draw_strokes(pen, strokes, stroke_width)
        pen = None
        
        glyph.removeOverlap()
        glyph.simplify()
        glyph_count += 1
    
    for char, (base, diacritic, offset) in EXTENDED_LATIN.items():
        unicode_val = ord(char)
        glyph = font.createChar(unicode_val)
        glyph.width = 900
        
        pen = glyph.glyphPen()
        create_composite_glyph(pen, base, diacritic, offset, stroke_width, font_data)
        pen = None
        
        glyph.removeOverlap()
        glyph.simplify()
        glyph_count += 1
    
    print(f"  Created {glyph_count} glyphs (Base: {len(font_data)}, Extended Latin: {len(EXTENDED_LATIN)})")
    
    return font


def create_sfd_file(output_path, font_data, stroke_width=40):
    """Create a FontForge SFD (source) file."""
    try:
        font = build_font_object(font_data, stroke_width)
        if font is None:
            return False
        
        print(f"Saving SFD file: {output_path}")
        font.save(str(output_path))
        
        print(f"Successfully created SFD file: {output_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_font_with_fontforge(output_path, font_data, stroke_width=40):
    """Create an OTF font file."""
    try:
        font = build_font_object(font_data, stroke_width)
        if font is None:
            return False
        
        print(f"Generating OTF file: {output_path}")
        font.generate(str(output_path))
        
        print(f"Successfully created OTF font: {output_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False




def generate_sfd_only():
    """Standalone function to generate only the SFD file."""
    script_dir = Path(__file__).parent
    r_file_path = script_dir / "create-arcade-font.R"
    sfd_path = script_dir / "ArcadeFont.sfd"
    
    print("Generating SFD file only...")
    print(f"Reading font data from: {r_file_path}")
    
    font_data = parse_r_font_file(r_file_path)
    print(f"Loaded {len(font_data)} base glyphs from R file")
    
    success = create_sfd_file(sfd_path, font_data, 40)
    
    if not success:
        sys.exit(1)


def main():
    script_dir = Path(__file__).parent
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        r_file_path = Path(sys.argv[1])
    else:
        r_file_path = script_dir / "create-arcade-font.R"
    
    # Ensure R file path is absolute
    if not r_file_path.is_absolute():
        r_file_path = script_dir / r_file_path
    
    otf_path = script_dir / "ArcadeFont.otf"
    
    print("=" * 60)
    print("Arcade Font Converter: Extended Edition")
    print("(Y-axis: NO flip - using R coordinates as-is)")
    print("=" * 60)
    print(f"Reading font data from: {r_file_path}")
    
    # Parse the R file to get font data
    font_data = parse_r_font_file(r_file_path)
    print(f"Loaded {len(font_data)} base glyphs from R file")
    
    success = create_font_with_fontforge(otf_path, font_data, 40)
    
    print("\n" + "=" * 60)
    if success:
        print("+ Font created with extended Latin characters")
        print(f"  File: {otf_path}")
    else:
        print("✗ Conversion failed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
