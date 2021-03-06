# vim:set et sts=4 sw=4:
# -*- coding: utf-8 -*-
#
# ibus-chewing - The Chewing engine for IBus
#
# Copyright (c) 2007-2008 Huang Peng <shawn.p.huang@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import gobject
import ibus
import chewing
from ibus import keysyms, modifier

_ = lambda a: a

class Engine(ibus.EngineBase):
    def __init__(self, bus, object_path):
        super(Engine, self).__init__(bus, object_path)

        # create chewing context
        self.__context = chewing.ChewingContext()
        self.__context.Configure(18, 16, "12345678")

        self.__lookup_table = ibus.LookupTable(8)
        self.__lookup_table.show_cursor(False)

        # init properties
        self.__chieng_property = ibus.Property("chieng")
        self.__letter_property = ibus.Property("letter")
        self.__kbtype_property = ibus.Property("kbtype")
        self.__prop_list = ibus.PropList()
        self.__prop_list.append(self.__chieng_property)
        self.__prop_list.append(self.__letter_property)
        self.__prop_list.append(self.__kbtype_property)

        # use reset to init values
        self.__reset()

    def __commit(self):
        # commit string
        if self.__context.keystrokeRtn & chewing.KEYSTROKE_COMMIT:
            text = u"".join(self.__context.commitStr)
            self.commit_string(text)

        # update preedit
        chiSymbolBuf = self.__context.chiSymbolBuf
        chiSymbolCursor = self.__context.chiSymbolCursor
        preedit_string = u"".join(
            chiSymbolBuf[:chiSymbolCursor] +
            self.__context.zuinBuf +
            chiSymbolBuf[chiSymbolCursor:])
        attrs = ibus.AttrList()
        attr = ibus.AttributeForeground(0xffffff,
            chiSymbolCursor, chiSymbolCursor + len(self.__context.zuinBuf))
        attrs.append(attr)
        attr = ibus.AttributeBackground(0x0,
            chiSymbolCursor, chiSymbolCursor + len(self.__context.zuinBuf))
        attrs.append(attr)
        attr = ibus.AttributeUnderline(ibus.ATTR_UNDERLINE_SINGLE,
            0, len(preedit_string))
        attrs.append(attr)
        self.update_preedit (preedit_string, attrs, chiSymbolCursor, len(preedit_string) > 0)

        # update lookup table
        self.__lookup_table.clean()
        ci = self.__context.ci
        if ci:
            for i in range(9):
                candidate = ci.get_candidate(i)
                if candidate:
                    self.__lookup_table.append_candidate(candidate)
            self.update_lookup_table (self.__lookup_table, True)
        else:
            self.update_lookup_table (self.__lookup_table, False)

        # update aux string
        text = u"".join(self.__context.showMsg)
        if text:
            self.update_aux_string(text, None, True)
        else:
            self.update_aux_string(u"", None, False)

        if self.__context.keystrokeRtn & chewing.KEYSTROKE_ABSORB:
            return True
        if self.__context.keystrokeRtn & chewing.KEYSTROKE_IGNORE:
            return False

        return True
    # reset values of engine
    def __reset(self):
        self.__lookup_table.clean()
        self.__context.Reset()
        self.__commit()

    def __refreash_chieng_property(self):
        if self.__context.get_ChiEngMode() == chewing.CHINESE_MODE:
            self.__chieng_property._label = _("Chi")
        else:
            self.__chieng_property._label = _("Eng")
        self.update_property(self.__chieng_property)

    def __refreash_letter_property(self):
        if self.__context.get_ShapeMode() == chewing.FULLSHAPE_MODE:
            self.__letter_property._label = _("Full")
        else:
            self.__letter_property._label = _("Half")
        self.update_property(self.__letter_property)

    def __refreash_kbtype_property(self):
        mode = self.__context.get_KBType()
        labels = {
            chewing.DEFAULT_KBTYPE: _("Default"),
            chewing.HSU_KBTYPE: _("Hsu's"),
            chewing.IBM_KBTYPE: _("IBM"),
            chewing.GINYIEH_KBTYPE: _("Gin-Yieh"),
            chewing.ETEN_KBTYPE: _("ETen"),
            chewing.ETEN26_KBTYPE: _("ETen 26-key"),
            chewing.DVORAK_KBTYPE: _("Dvorak"),
            chewing.DVORAKHSU_KBTYPE: _("Dvorak Hsu's"),
            chewing.HANYU_KBTYPE: _("Han-Yu"),
        }
        self.__kbtype_property._label = labels.get(mode, _("Default"))
        self.update_property(self.__kbtype_property)

    def __refreash_properties(self):
        self.__refreash_chieng_property()
        self.__refreash_letter_property()
        self.__refreash_kbtype_property()

    def page_up(self):
        self.__context.handle_PageUp()
        self.__commit()
        return True

    def page_down(self):
        self.__context.handle_PageDown()
        self.__commit()
        return True

    def cursor_up(self):
        self.__context.handle_Up()
        self.__commit()
        return True

    def cursor_down(self):
        self.__context.handle_Down()
        self.__commit()
        return True

    def process_key_event(self, keyval, is_press, state):
        # ignore key release events
        if not is_press:
            return False
        state = state & (modifier.SHIFT_MASK | modifier.CONTROL_MASK | modifier.MOD1_MASK)

        if state == 0:
            if keyval == keysyms.Return:
                self.__context.handle_Enter()
            elif keyval == keysyms.Escape:
                self.__context.handle_Esc()
            elif keyval == keysyms.BackSpace:
                self.__context.handle_Backspace()
            elif keyval == keysyms.Delete or keyval == keysyms.KP_Delete:
                self.__context.handle_Del()
            elif keyval == keysyms.space or keyval == keysyms.KP_Space:
                self.__context.handle_Space()
            elif keyval == keysyms.Page_Up or keyval == keysyms.KP_Page_Up:
                self.__context.handle_PageUp()
            elif keyval == keysyms.Page_Down or keyval == keysyms.KP_Page_Down:
                self.__context.handle_PageDown()
            elif keyval == keysyms.Up or keyval == keysyms.KP_Up:
                self.__context.handle_Up()
            elif keyval == keysyms.Down or keyval == keysyms.KP_Down:
                self.__context.handle_Down()
            elif keyval == keysyms.Left:
                self.__context.handle_Left()
            elif keyval == keysyms.Right:
                self.__context.handle_Right()
            elif keyval == keysyms.Home or keyval == keysyms.KP_Home:
                self.__context.handle_Home()
            elif keyval == keysyms.End or keyval == keysyms.KP_End:
                self.__context.handle_End()
            elif keyval == keysyms.Tab:
                self.__context.handle_Tab()
            else:
                self.__context.handle_Default(keyval)
        elif state == modifier.SHIFT_MASK:
            if keyval == keysyms.Shift_L:
                self.__context.handle_ShiftLeft()
            elif keyval == keysyms.Shift_R:
                self.__context.handle_ShiftRight()
            elif keyval == keysyms.space or keyval == keysyms.KP_Space:
                self.__context.handle_ShiftSpace()
                self.property_activate("letter")
            else:
                self.__context.handle_Default(keyval)
        elif state == modifier.CONTROL_MASK:
            if keyval >= keysyms._0 and keyval <= keysyms._9:
                self.__context.handle_CtrlNum(keyval)
            else:
                return False
        else:
            return False

        return self.__commit()

    def focus_in(self):
        self.register_properties(self.__prop_list)
        self.__refreash_properties()

    def focus_out(self):
        pass

    def property_activate(self, prop_name, prop_state = ibus.PROP_STATE_UNCHECKED):
        if prop_name == "chieng":
            if self.__context.get_ChiEngMode() == chewing.CHINESE_MODE:
                self.__context.set_ChiEngMode(chewing.SYMBOL_MODE)
            else:
                self.__context.set_ChiEngMode(chewing.CHINESE_MODE)
        elif prop_name == "letter":
            if self.__context.get_ShapeMode() == chewing.FULLSHAPE_MODE:
                self.__context.set_ShapeMode(chewing.HALFSHAPE_MODE)
            else:
                self.__context.set_ShapeMode(chewing.FULLSHAPE_MODE)
        elif prop_name == "kbtype":
            _type = self.__context.get_KBType()
            if _type == chewing.LAST_KBTYPE:
                _type = chewing.FIRST_KBTYPE
            else:
                _type += 1
            self.__context.set_KBType(_type)
        self.__refreash_properties()

