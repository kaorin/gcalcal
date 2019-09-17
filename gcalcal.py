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
from datetime import date, timedelta
from os.path import abspath, dirname, join

WHERE_AM_I = abspath(dirname(__file__))
GCAL_PATH="~/.local/bin/"
EVENT_CALENDAR="kaoru.konno@gmail.com"
HOLIDAY_CALENDAR="日本の祝日"

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
        self.mainWindow = self.wMain.get_object ("wCalendar")
        self.calCalendar = self.wMain.get_object ("calCalendar")
        self.txtBuffer = self.wMain.get_object ("txtInfoBuffer")
        self.schedule = self.wMain.get_object ("txtInfoText")
        self.lblMonth = self.wMain.get_object ("lblMonth")
        self.lblYear = self.wMain.get_object ("lblYear")
        lblNo = 0
        self.days = [[0 for i in range(7)] for j in range(7)]
        for row in range(6):
            for col in range(7):
                self.days[row][col] = self.wMain.get_object ("lbl{:02d}".format(lblNo))
                lblNo += 1
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
            "on_wCalendar_destroy" : self.on_MainWindow_destroy,
            "on_wCalendar_button_press_event" : self.on_MainWindow_button_press_event,
            "on_wCalendar_realize" : self.on_MainWindow_realize,
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
            "on_evMonthDown_button_release_event": self.on_evMonthDown_button_release_event,
            "on_evMonthUp_button_release_event": self.on_evMonthUp_button_release_event,
            "on_evYearDonw_button_release_event": self.on_evYearDonw_button_release_event,
            "on_evYearUp_button_release_event": self.on_evYearUp_button_release_event,
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
        self.month = now.month
        self.year = now.year
        self.set_style()
        self.makeCalendar(now.year, now.month)
        self.mainWindow.show_all()

    def makeCalendar(self,year,month):
        self.initDayStyle()
        calendar.setfirstweekday(calendar.SUNDAY)
        self.lblMonth.set_text(calendar.month_name[month])
        self.lblYear.set_text(str(year))
        cal = calendar.monthcalendar(year, month)
        firstWeek, lastday = calendar.monthrange(year,month)
        prevdate = date(year,month,1) - timedelta(days=1)
        nextdate = date(year,month,lastday) + timedelta(days=1)
        prevcal = calendar.monthcalendar(prevdate.year, prevdate.month)
        nextcal = calendar.monthcalendar(nextdate.year, nextdate.month)
        start = 0
        if firstWeek == 6:
            start = 1
        calRow = 0
        for row in range(start, 6):
            for col in range(7):
                if cal[calRow][col] != 0:
                    self.days[row][col].set_text(str(cal[calRow][col]))
                    if date.today() == date(year, month, cal[calRow][col]):
                        css_context = self.days[row][col].get_style_context()
                        css_context.add_class("today")
            calRow += 1
            if len(cal) <= calRow:
                break
        # 前月
        prevLastRow = len(prevcal)
        for col in range(7):
            if prevcal[prevLastRow - 1][col] != 0:
                self.days[0][col].set_text(str(prevcal[prevLastRow - 1][col]))
                css_context = self.days[0][col].get_style_context()
                css_context.add_class("prev_month")
        # 次月
        lastrow = len(cal) - 1 + start
        start = 0
        if firstWeek != 6:
            start = 1
        for row in range(6 - len(cal) + start):
            for col in range(7):
                if nextcal[row][col] != 0:
                    self.days[lastrow+row][col].set_text(str(nextcal[row][col]))
                    css_context = self.days[lastrow+row][col].get_style_context()
                    css_context.add_class("next_month")
        self.setEventDay()
        self.setEventDayList()
        self.setHolidayList()
        
    def initDayStyle(self):
        for row in range(6):
            for col in range(7):
                css_context = self.days[row][col].get_style_context()
                css_context.remove_class("today")
                css_context.remove_class("holiday")
                css_context.remove_class("prev_month")
                css_context.remove_class("next_month")
                css_context.remove_class("selected")
                css_context.remove_class("marked")

    def findDayLabel(self, day):
        for row in range(6):
            for col in range(7):
                css_context = self.days[row][col].get_style_context()
                if css_context.has_class("prev_month") == False and css_context.has_class("next_month") == False:
                    if int(self.days[row][col].get_text()) == day:
                        return self.days[row][col]
        return None

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip):
        text = widget.get_tooltip_text()
        tooltip.set_text(text)
        return True

    def setHoliday(self, day, text):
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        css_context.add_class("holiday")
        day.set_has_tooltip(True)
        day.set_tooltip_text(text)
        day.connect("query-tooltip", self.tooltip_callback)


    def setMarked(self, day, text):
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        css_context.add_class("marked")
        day.set_has_tooltip(True)
        day.set_tooltip_text(text)
        day.connect("query-tooltip", self.tooltip_callback)

    def on_evMonthDown_button_release_event(self, wdget, event):
        prevdate = date(self.year,self.month,1) - timedelta(days=1)
        self.month = prevdate.month
        self.year = prevdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evMonthUp_button_release_event(self, wdget, event):
        firstWeek, lastday = calendar.monthrange(self.year, self.month)
        nextdate = date(self.year,self.month,lastday) + timedelta(days=1)
        self.month = nextdate.month
        self.year = nextdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearDonw_button_release_event(self, wdget, event):
        self.year -= 1
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearUp_button_release_event(self, wdget, event):
        self.year += 1
        self.makeCalendar(self.year, self.month)
        return


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
        self.montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        self.montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + EVENT_CALENDAR + "\" --nocolor agenda " + self.montStart.isoformat() + " " + self.montFinish.isoformat())
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split()
                if len(info) > 2:
                    self.setMarked(int(info[2]), " ".join(info[3:]))
    
    def setEventDayList(self):
        self.montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        self.montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli --nocolor agenda " + self.montStart.isoformat() + " " + self.montFinish.isoformat())
        text = ""
        for sch in schedules:
            if len(sch) > 0:
                text += sch + "\n"
        self.txtBuffer.set_text(text)

    def setHolidayList(self):
        self.montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        self.montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + HOLIDAY_CALENDAR + "\" --nocolor agenda " + self.montStart.isoformat() + " " + self.montFinish.isoformat())
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split()
                if len(info) > 2:
                    self.setHoliday(int(info[2]), " ".join(info[3:]))

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
