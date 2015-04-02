#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Author: Tomokuni SEKIYA
#

# version
newfont_version      = "2.007.20150313"
newfont_sfntRevision = 0x00010000

# set font name
newfontM  = ("../Myrica-MM.ttf", "Myrica-MM", "Myrica MM", "Myrica MM")

# source file
srcfontIncosolata   = "../SourceTTF/Inconsolata-Powerline-Regular.ttf"
srcfontGenShin      = "../SourceTTF/mgenplus-1m-regular.ttf"
srcfontReplaceParts = "myricaM_ReplaceParts.ttf"

# flag
scalingDownIfWidth_flag = True

# set ascent and descent (line width parameters)
newfont_ascent  = 840
newfont_descent = 184
newfont_em = newfont_ascent + newfont_descent

newfont_winAscent   = 840
newfont_winDescent  = 170
newfont_typoAscent  = newfont_winAscent
newfont_typoDescent = -newfont_winDescent
newfont_typoLinegap = 0
newfont_hheaAscent  = newfont_winAscent
newfont_hheaDescent = -newfont_winDescent
newfont_hheaLinegap = 0

# define
generate_flags = ('opentype', 'PfEd-lookups', 'TeX-table')
panoseBase = (2, 11, 5, 9, 2, 2, 3, 2, 2, 7)

########################################
# setting
########################################

import copy
import os
import sys
import shutil
import fontforge
import psMat

# 縦書きのために指定する
fontforge.setPrefs('CoverageFormatsAllowed', 1)
# 大変更時に命令を消去 0:オフ 1:オン
fontforge.setPrefs('ClearInstrsBigChanges', 0)
# TrueType命令をコピー 0:オフ 1:オン
fontforge.setPrefs('CopyTTFInstrs', 1)

########################################
# pre-process
########################################

print
print
print "myrica generator " + newfont_version
print
print "This script is for generating 'myrica' font"
print
if os.path.exists( srcfontIncosolata ) == False:
    print "Error: " + srcfontIncosolata + " not found"
    sys.exit( 1 )
if os.path.exists( srcfontReplaceParts ) == False:
    print "Error: " + srcfontReplaceParts + " not found"
    sys.exit( 1 )
if os.path.exists( srcfontGenShin ) == False:
    print "Error: " + srcfontGenShin + " not found"
    sys.exit( 1 )

########################################
# define function
########################################

def matRescale(origin_x, origin_y, scale_x, scale_y):
    return psMat.compose(
        psMat.translate(-origin_x, -origin_y), psMat.compose(
        psMat.scale(scale_x, scale_y),
        psMat.translate(origin_x, origin_y)))

def matMove(move_x, move_y):
    return psMat.translate(move_x, move_y)

def rng(start, end):
    return range(start, end + 1)

def flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)):
            for f in flatten(e):
                yield f
        else:
            yield e

def select(font, *codes):
    font.selection.none()
    selectMore(font, codes)

def selectMore(font, *codes):
    flat = flatten(codes)
    for c in flat:
        if isinstance(c, (unicode, )):
            font.selection.select(("more",), ord(c))
        else:
            font.selection.select(("more",), c)

def selectLess(font, *codes):
    flat = flatten(codes)
    for c in flat:
        if isinstance(c, (unicode, )):
            font.selection.select(("less",), ord(c))
        else:
            font.selection.select(("less",), c)

def selectExistAll(font):
    font.selection.none()
    for glyphName in font:
        if font[glyphName].isWorthOutputting() == True:
            font.selection.select(("more",), glyphName)

def copyAndPaste(srcFont, srcCodes, dstFont, dstCodes):
    select(srcFont, srcCodes)
    srcFont.copy()
    select(dstFont, dstCodes)
    dstFont.paste()

def copyAndPasteInto(srcFont, srcCodes, dstFont, dstCodes, pos_x, pos_y):
    select(srcFont, srcCodes)
    srcFont.copy()
    select(dstFont, dstCodes)
    dstFont.transform(matMove(-pos_x, -pos_y))
    dstFont.pasteInto()
    dstFont.transform(matMove(pos_x, pos_y))

def scalingDownIfWidth(font, scaleX, scaleY):
    for glyph in font.selection.byGlyphs:
        width = glyph.width
        glyph.transform(matRescale(width / 2, 0, scaleX, scaleY))
        glyph.width = width

def centerInWidth(font):
    for glyph in font.selection.byGlyphs:
        w  = glyph.width
        wc = w / 2
        bb = glyph.boundingBox()
        bc = (bb[0] + bb[2]) / 2
        glyph.transform(matMove(wc - bc, 0))
        glyph.width = w

def setWidth(font, width):
    for glyph in font.selection.byGlyphs:
        glyph.width = width

def setAutoWidthGlyph(glyph, separation):
    bb = glyph.boundingBox()
    bc = (bb[0] + bb[2]) / 2
    nw = (bb[2] - bb[0]) + separation * 2
    if glyph.width > nw:
        wc = nw / 2
        glyph.transform(matMove(wc - bc, 0))
        glyph.width = nw

def autoHintAndInstr(font, *codes):
    removeHintAndInstr(font, codes)
    font.autoHint()
    font.autoInstr()

def removeHintAndInstr(font, *codes):
    select(font, codes)
    for glyph in font.selection.byGlyphs:
        if glyph.isWorthOutputting() == True:
            glyph.manualHints = False
            glyph.ttinstrs = ()
            glyph.dhints = ()
            glyph.hhints = ()
            glyph.vhints = ()

def copyTti(srcFont, dstFont):
    for glyphName in dstFont:
        dstFont.setTableData('fpgm', srcFont.getTableData('fpgm'))
        dstFont.setTableData('prep', srcFont.getTableData('prep'))
        dstFont.setTableData('cvt',  srcFont.getTableData('cvt'))
        dstFont.setTableData('maxp', srcFont.getTableData('maxp'))
        copyTtiByGlyphName(srcFont, dstFont, glyphName)

def copyTtiByGlyphName(srcFont, dstFont, glyphName):
    try:
        dstGlyph = dstFont[glyphName]
        srcGlyph = srcFont[glyphName]
        if srcGlyph.isWorthOutputting() == True and dstGlyph.isWorthOutputting() == True:
            dstGlyph.manualHints = True
            dstGlyph.ttinstrs = srcFont[glyphName].ttinstrs
            dstGlyph.dhints = srcFont[glyphName].dhints
            dstGlyph.hhints = srcFont[glyphName].hhints
            dstGlyph.vhints = srcFont[glyphName].vhints
    except TypeError:
        pass

def setFontProp(font, fontInfo):
    font.fontname   = fontInfo[1]
    font.familyname = fontInfo[2]
    font.fullname   = fontInfo[3]
    font.weight = "Book"
    font.copyright =  "Copyright (c) 2006-2012 Raph Levien (Inconsolata)\n"
    font.copyright += "Copyright (c) 2013 M+ FONTS PROJECT (M+)\n"
    font.copyright += "Copyright (c) 2013 itouhiro (Migu)\n"
    font.copyright += "Copyright (c) 2014 MM (Mgen+)\n"
    font.copyright += "Copyright (c) 2014 Adobe Systems Incorporated. (NotoSansJP)\n"
    font.copyright += "Licenses:\n"
    font.copyright += "SIL Open Font License Version 1.1 "
    font.copyright += "(http://scripts.sil.org/ofl)\n"
    font.copyright += "Apache License, Version 2.0 "
    font.copyright += "(http://www.apache.org/licenses/LICENSE-2.0)"
    font.version = newfont_version
    font.sfntRevision = newfont_sfntRevision
    font.sfnt_names = (('English (US)', 'UniqueID', fontInfo[2]), )
    #('Japanese', 'PostScriptName', fontInfo[2]),
    #('Japanese', 'Family', fontInfo[1]),
    #('Japanese', 'Fullname', fontInfo[3]),

    font.hasvmetrics = True
    font.head_optimized_for_cleartype = True

    font.os2_panose = panoseBase
    font.os2_vendor = "M+"
    font.os2_version = 1

    font.os2_winascent       = newfont_winAscent
    font.os2_winascent_add   = 0
    font.os2_windescent      = newfont_winDescent
    font.os2_windescent_add  = 0
    font.os2_typoascent      = newfont_typoAscent
    font.os2_typoascent_add  = 0
    font.os2_typodescent     = -newfont_typoDescent
    font.os2_typodescent_add = 0
    font.os2_typolinegap     = newfont_typoLinegap
    font.hhea_ascent         = newfont_hheaAscent
    font.hhea_ascent_add     = 0
    font.hhea_descent        = -newfont_hheaDescent
    font.hhea_descent_add    = 0
    font.hhea_linegap        = newfont_hheaLinegap

charASCII  = rng(0x0021, 0x007E)
charZHKana = list(u"ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん"),
charZKKana = list(u"ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶ"),
charHKKana = list(u"､｡･ｰﾞﾟ｢｣ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｧｨｩｪｫｬｭｮｯ")
charZEisu = list(u"０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ")

########################################
# modified ReplaceParts
########################################

print
print "Open " + srcfontReplaceParts
fRp = fontforge.open( srcfontReplaceParts )

# modify em
fRp.em  = newfont_em
fRp.ascent  = newfont_ascent
fRp.descent = newfont_descent

# post-process
fRp.selection.all()
fRp.round()

#fRp.generate("../Work/modReplaceParts.ttf", '', generate_flags)

########################################
# modified Inconsolata
########################################

print
print "Open " + srcfontIncosolata
fIn = fontforge.open( srcfontIncosolata )

# modify
print "modify"

# 拡大 "'`
select(fIn, 0x0022, 0x0027, 0x0060)
fIn.transform(matRescale(250, 600, 1.1, 1.1))
setWidth(fIn, 1000 / 2)

# 拡大 ,.:;
select(fIn, 0x002c, 0x002e, 0x003a, 0x003b)
fIn.transform(matRescale(250, 0, 1.1, 1.1))
setWidth(fIn, 1000 / 2)

# 移動 ~
select(fIn, 0x007e)
fIn.transform(matMove(0, 110))

# 文字の置換え
print "merge ReplaceParts"
for glyph in fRp.glyphs():
    if glyph.unicode == 0x006c:
        select(fRp, glyph.glyphname)
        fRp.copy()
        select(fIn, glyph.glyphname)
        fIn.paste()

# 必要文字だけを残して削除
select(fIn, 0x0021, rng(0x0023, 0x0026), rng(0x0028, 0x007E), rng(0xE0A0, 0xE0BF))
fIn.selection.invert()
fIn.clear()

# modify em
fIn.em  = newfont_em
fIn.ascent  = newfont_ascent
fIn.descent = newfont_descent

# post-process
fIn.selection.all()
fIn.round()

#fIn.generate("../Work/modIncosolata.ttf", '', generate_flags)

########################################
# modified Mgen+
########################################

print
print "Open " + srcfontGenShin
fGs = fontforge.open( srcfontGenShin )

# modify
print "modify"

# 拡大 "'
select(fGs, 0x0022, 0x0027)
fGs.transform(matRescale(256, 656, 1.1, 1.1))
setWidth(fGs, 1024 / 2)

# scaling down
if scalingDownIfWidth_flag == True:
    print "While scaling, wait a little..."
    # 0.91はRictyに準じた。
    selectExistAll(fGs)
    selectLess(fGs, (charASCII, charHKKana, charZHKana, charZKKana, charZEisu))
    scalingDownIfWidth(fGs, 0.91, 0.91)
    # 平仮名/片仮名のサイズを調整
    select(fGs, (charZHKana,charZKKana))
    scalingDownIfWidth(fGs, 0.96, 0.96)
    # 全角英数の高さを調整 (半角英数の高さに合わせる)
    select(fGs, charZEisu)
    scalingDownIfWidth(fGs, 0.91, 0.86)

# 移動
selectExistAll(fGs)
fGs.transform(matMove(0, -32))

#fGs.generate("../Work/modGenShin.ttf", '', generate_flags)

########################################
# create MyricaM Monospace
########################################
fMm = fIn

print
print "Build " + newfontM[0]

# pre-process
setFontProp(fMm, newfontM)

# merge Mgen+
print "merge Mgen+"

# マージ
fMm.mergeFonts( srcfontGenShin )
fMm.os2_unicoderanges = fGs.os2_unicoderanges
fMm.os2_codepages = fGs.os2_codepages

# ルックアップテーブルの置換え
for l in fGs.gsub_lookups:
    fMm.importLookups(fGs, l)
for l in fMm.gsub_lookups:
    if l.startswith(fGs.fontname + "-") == True:
        fMm.removeLookup(l)
#for l in fMm.gpos_lookups:
#    fMm.removeLookup(l)
#for l in fGs.gpos_lookups:
#    fMm.importLookups(fGs, l)

# generate
print "Generate " + newfontM[0]
fMm.generate(newfontM[0], '', generate_flags)

fMm.close()
fGs.close()
fRp.close()
