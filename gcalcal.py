#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from xml.dom import minidom
import codecs
import base64
import subprocess
import calendar
import datetime
from datetime import date
from os.path import abspath, dirname, join

WHERE_AM_I = abspath(dirname(__file__))
GCAL_PATH="~/.local/bin/"

class ConfigXML:
    OptionList = {   "x_pos":"40",
                     "y_pos":"40",
                     "width":"320",
                     "height":"200",
                     "opacity":"100%",
                     "decoration":"True",
    }
    AppName = "Gcalcal"
    ConfigPath = "/.config/Gcalcal.xml"
    Options = {}    #オプション値の辞書
    domobj = None

    def __init__(self, read):
        #print "ConfigXML"
        if read == True:
            try:
                self.domobj = minidom.parse(os.path.abspath(os.path.expanduser("~") + self.ConfigPath))
                options = self.domobj.getElementsByTagName("options")
                for opt in options :
                    for op,defVal in self.OptionList.items():
                        elm = opt.getElementsByTagName(op)
                        if len(elm) > 0 :
                            self.Options[op] = self.getText(elm[0].childNodes)
                        else:
                            self.Options[op] = defVal
            except Exception as e:
                print(e)
                for op,defVal in self.OptionList.items():
                    self.Options[op] = defVal

    def getText(self,nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                text = str(node.data)
                text = text.rstrip(" \t\n")
                text = text.lstrip(" \t\n")
                rc = rc + text
        return rc

    def GetOption(self, optName ):
        if optName == "password":
            return str(base64.b64decode(self.Options[optName]))
        else:
            try:
                return str(self.Options[optName])
            except:
                return str(self.OptionList[optName])

    def SetOption(self, optName, value ):
        if optName == "password":
            val = base64.b64encode(value)
            self.Options[optName] = val
        else:
            self.Options[optName] = value

    def Write(self):
        try:
            impl = minidom.getDOMImplementation()
            newdoc = impl.createDocument(None, self.AppName, None)
            root = newdoc.documentElement
            opts = newdoc.createElement("options")
            root.appendChild(opts)
            for op in self.OptionList.keys():
                opt = newdoc.createElement(op)
                opts.appendChild(opt)
                text = newdoc.createTextNode(str(self.Options[op]))
                opt.appendChild(text)
            file = codecs.open(os.path.abspath(os.path.expanduser("~") + self.ConfigPath), 'wb', encoding='utf-8')
            newdoc.writexml(file, '', '\t', '\n', encoding='utf-8')
        except:
            print ("Error Config Write")

class myCalendar:

    def __init__(self):
        """

        """
        conf = ConfigXML(True)
        #メインウィンドウを作成
        self.wMain = Gtk.Builder()
        self.wMain.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/gcalcal.glade")
        self.context_menu =  self.wMain.get_object ("mMenu")
        self.mainWindow = self.wMain.get_object ("MainWindow")
        self.calCalendar = self.wMain.get_object ("calCalendar")
        self.txtBuffer = self.wMain.get_object ("txtBuffer")
        self.schedule = self.wMain.get_object ("txtSchedule")
        # GdkColormap to GdkVisual
        # なんか透過ウィンドウを作成するのはこれがミソっぽい
        screen = self.mainWindow.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.mainWindow.set_visual(visual)
        else:
            print ("no Composited...")
        dic = {
            "on_miExit_activate" : self.on_miExit_activate,
            "on_MainWindow_destroy" : self.on_MainWindow_destroy,
            "on_MainWindow_button_press_event" : self.on_MainWindow_button_press_event,
            "on_calCalender_day_selected" : self.on_calCalender_day_selected,
            "on_calCalender_day_selected_double_click" : self.on_calCalender_day_selected_double_click,
            "on_calCalender_month_changed" : self.on_calCalender_month_changed,
            "on_calCalender_next_month" : self.on_calCalender_month_changed,
            "on_calCalender_prev_month" : self.on_calCalender_month_changed,
            "on_calCalender_next_year" : self.on_calCalender_month_changed,
            "on_calCalender_prev_year" : self.on_calCalender_month_changed,
            "on_MainWindow_realize" : self.on_MainWindow_realize,
            "on_miTitlebar_toggled" : self.on_miTitlebar_toggled,
            "on_mi010_activate" : self.on_miOpacity_activate,
            "on_mi020_activate" : self.on_miOpacity_activate,
            "on_mi030_activate" : self.on_miOpacity_activate,
            "on_mi040_activate" : self.on_miOpacity_activate,
            "on_mi050_activate" : self.on_miOpacity_activate,
            "on_mi060_activate" : self.on_miOpacity_activate,
            "on_mi070_activate" : self.on_miOpacity_activate,
            "on_mi080_activate" : self.on_miOpacity_activate,
            "on_mi090_activate" : self.on_miOpacity_activate,
            "on_mi100_activate" : self.on_miOpacity_activate,
            "on_MainWindow_focus_out_event": self.on_MainWindow_focus_out_event,
        }
        self.wMain.connect_signals(dic)
        xpos = conf.GetOption("x_pos")
        ypos = conf.GetOption("y_pos")
        self.w = int(conf.GetOption("width"))
        self.h = int(conf.GetOption("height"))
        self.decoration = eval(conf.GetOption("decoration"))
        self.mainWindow.move(int(xpos), int(ypos))
        self.canselEvent = True
        self.mainWindow.resize(self.w,self.h)
        self.canselEvent = False
        self.opacity = float(conf.GetOption("opacity").replace("%","")) / 100
        self.mainWindow.set_opacity(self.opacity)
        self.schedule.set_opacity(self.opacity)
        self.mainWindow.set_decorated(self.decoration)
        now = date.today()
        self.calCalendar.select_month(now.year, now.month)
        self.calCalendar.select_day(now.day)
        self.setEventDay()
        self.set_style()
        self.mainWindow.show_all()

    def on_MainWindow_button_press_event(self,widget,event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            #右クリック
            self.context_menu.popup(None, None, None,None, event.button, event.time)

    def on_miTitlebar_toggled(self, widget):
        self.decoration = widget.get_active()
        self.mainWindow.set_decorated(self.decoration)
        return

    def on_miOpacity_activate(self, widget):
        menuStr = widget.get_child().get_text()
        self.opacity = float(menuStr.replace("%","")) / 100
        self.mainWindow.set_opacity(self.opacity)
        self.schedule.set_opacity(self.opacity)
        return

    def _saveConf(self):
        conf = ConfigXML(False)
        (xpos, ypos) = self.mainWindow.get_position()
        (self.w, self.h) = self.mainWindow.get_size()
        conf.SetOption("x_pos",xpos)
        conf.SetOption("y_pos",ypos)
        conf.SetOption("width",self.w)
        conf.SetOption("height",self.h)
        conf.SetOption("opacity",str(self.opacity*100) + "%")
        conf.SetOption("decoration",str(self.decoration))
        conf.Write()

    def on_MainWindow_realize(self, widget):
        if self.canselEvent == True:
            return
        self._saveConf()
        return

    def on_MainWindow_focus_out_event(self, widget, event):
        if self.canselEvent == True:
            return
        self._saveConf()
        self.canselEvent = False
        return

    def setEventDay(self):
        (year, month, day) = self.calCalendar.get_date()
        self.montStart = date(year,month + 1,1)
        _, lastday = calendar.monthrange(year,month + 1)
        self.montFinish = date(year,month + 1,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli --nocolor agenda " + self.montStart.isoformat() + " " + self.montFinish.isoformat())
        text = ""
        # イベントマークをクリア
        self.calCalendar.clear_marks()
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split()
                if len(info) > 2:
                    self.calCalendar.mark_day(int(info[2]))
                text += sch + "\n"
        self.txtBuffer.set_text(text)
    
    def on_calCalender_day_selected(self,widget):
        return

    def on_calCalender_day_selected_double_click(self,widget):
        return

    def on_calCalender_month_changed(self,widget):
        self.setEventDay()
        return

    def on_miExit_activate(self,widget):
        self._saveConf()
        Gtk.main_quit()

    def on_MainWindow_destroy(self,widget):
        Gtk.main_quit()

    def res_cmd(self, cmd):
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).communicate()[0].decode("utf-8", "ignore")

    def res_cmd_lfeed(self, cmd):
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).stdout.readlines()

    def res_cmd_no_lfeed(self, cmd):
        return [bytes(x).decode("utf-8", "ignore").rstrip("\n") for x in self.res_cmd_lfeed(cmd)]

    def set_style(self):
        """
        Change Gtk+ Style
        """
        provider = Gtk.CssProvider()
        # Demo CSS kindly provided by Numix project
        provider.load_from_path(join(WHERE_AM_I, 'gcalcal.css'))
        screen = Gdk.Display.get_default_screen(Gdk.Display.get_default())
        # I was unable to found instrospected version of this
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

if __name__ == '__main__':
    myCalendar()
    Gtk.main()
