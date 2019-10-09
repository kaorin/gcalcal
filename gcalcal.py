#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf
from xml.dom import minidom
import codecs
import base64
import subprocess
import calendar
import datetime
import cairo
from datetime import datetime, date, timedelta
from os.path import abspath, dirname, join
import random

__VERSION__="1.0.0.0"

WHERE_AM_I = abspath(dirname(__file__))
GCAL_PATH="~/.local/bin"
EVENT_CALENDAR="kaoru.konno@gmail.com"
HOLIDAY_CALENDAR="日本の祝日"
WALLPAPER_PATH = ""

class ConfigXML:
    OptionList = {
        "x_pos":"40",
        "y_pos":"40",
        "width":"320",
        "height":"200",
        "opacity":"100%",
        "decoration":"True",
        "gcal_path":"",
        "event_calendar":"xxx@gmail.com",
        "holiday_calendar":"日本の祝日",
        "bgColor":"#000000",
        "mdColor":"#FFFF00",
        "tmColor":"#80FF80",
        "textColor":"#FFFFFF",
        "wallpaper_path":"/usr/share/backgrounds",
        "use_wallpaper":"",
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
    """カレンダークラス
    Returns:
        [type] -- [description]
    """
    wallpaper_list = []
    wlist = []
    sw = 0
    use_wallpaper_list = []
    #timeout_interval = 10
    timeout_interval = 1

    def __init__(self):
        """初期化
        """

        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        global WALLPAPER_PATH
        conf = ConfigXML(True)
        WALLPAPER_PATH = conf.GetOption("wallpaper_path")
        uselist = conf.GetOption("use_wallpaper")
        #メインウィンドウを作成
        self.wMain = Gtk.Builder()
        self.wMain.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/gcalcal.glade")
        self.context_menu =  self.wMain.get_object ("mMenu")
        self.mainWindow = Gtk.Window()
        self.mainWindow.set_title("透明カレンダー")
        self.mainWindow.set_skip_taskbar_hint(True)
        self.mainWindow.set_skip_pager_hint(True)
        css_context = self.mainWindow.get_style_context()
        css_context.add_class("mainWindow")
        self.vbxMain = self.wMain.get_object ("vbxMain")
        self.mainWindow.add(self.vbxMain)
        self.calCalendar = self.wMain.get_object ("calCalendar")
        self.sclInfoText = self.wMain.get_object ("sclInfoText")
        self.txtBuffer = self.wMain.get_object ("txtInfoBuffer")
        self.schedule = self.wMain.get_object ("txtInfoText")
        self.lblMonth = self.wMain.get_object ("lblMonth")
        self.lblYear = self.wMain.get_object ("lblYear")
        self.cmbMonth = self.wMain.get_object ("cmbMonth")
        self.cmbYear = self.wMain.get_object ("cmbYear")
        for month_name in calendar.month_name[1:]:
            self.cmbMonth.append(None, month_name)
        self.cmbMonth.set_active(date.today().month - 1)
        for y in range(-5, 5):
            self.cmbYear.append(str(date.today().year + y), str(date.today().year + y))
        self.cmbYear.set_active_id(str(date.today().year))
        lblNo = 0
        self.days = [[0 for i in range(7)] for j in range(7)]
        for row in range(6):
            for col in range(7):
                self.days[row][col] = self.wMain.get_object ("lbl{:02d}".format(lblNo))
                self.wMain.get_object("ev{:02d}".format(lblNo)).connect("button_press_event", self.on_day_button_press_event)
                lblNo += 1
        # GdkColormap to GdkVisual
        # なんか透過ウィンドウを作成するのはこれがミソっぽい
        screen = self.mainWindow.get_screen()
        visual = screen.get_rgba_visual()
        if visual != None and screen.is_composited():
            self.mainWindow.set_visual(visual)
            self.supports_alpha = True
        else:
            self.supports_alpha = False
            print ("no Composited...")
        dic = {
            "on_miExit_activate" : self.on_miExit_activate,
            "on_miSetting_activate" : self.on_miSetting_activate,
            "on_wCalendar_destroy" : self.on_wCalendar_destroy,
            "on_wCalendar_button_press_event" : self.on_wCalendar_button_press_event,
            "on_wCalendar_realize" : self.on_MainWindow_realize,
            "on_miTitlebar_toggled" : self.on_miTitlebar_toggled,
            "on_wCalendar_focus_out_event": self.on_wCalendar_focus_out_event,
            "on_evMonthDown_button_release_event": self.on_evMonthDown_button_release_event,
            "on_evMonthUp_button_release_event": self.on_evMonthUp_button_release_event,
            "on_evYearDonw_button_release_event": self.on_evYearDonw_button_release_event,
            "on_evYearUp_button_release_event": self.on_evYearUp_button_release_event,
            "on_evMonth_button_press_event": self.on_evMonth_button_press_event,
            "on_evYear_button_press_event": self.on_evYear_button_press_event,
            "on_cmbMonth_changed": self.on_cmbMonth_changed,
            "on_cmbYear_changed": self.on_cmbYear_changed,
            "on_cmbMonth_popdown": self.on_cmbMonth_popdown,
            "on_cmbYear_popdown": self.on_cmbYear_popdown,
        }
        self.wMain.connect_signals(dic)
        self.mainWindow.connect("draw", self.on_draw)
        self.mainWindow.connect("destroy",self.on_wCalendar_destroy)
        self.mainWindow.connect("button_press_event",self.on_wCalendar_button_press_event)
        self.mainWindow.connect("realize",self.on_MainWindow_realize)
        xpos = conf.GetOption("x_pos")
        ypos = conf.GetOption("y_pos")
        self.w = int(conf.GetOption("width"))
        self.h = int(conf.GetOption("height"))
        self.decoration = eval(conf.GetOption("decoration"))
        GCAL_PATH = conf.GetOption("gcal_path")
        EVENT_CALENDAR = conf.GetOption("event_calendar")
        HOLIDAY_CALENDAR = conf.GetOption("holiday_calendar")
        self.bgColor = Gdk.color_parse(conf.GetOption("bgColor"))
        self.mdColor = Gdk.color_parse(conf.GetOption("mdColor"))
        self.tmColor = Gdk.color_parse(conf.GetOption("tmColor"))
        self.textColor = Gdk.color_parse(conf.GetOption("textColor"))
        self.cancalEvent = True
        self.mainWindow.resize(self.w,self.h)
        self.wMain.get_object("miTitlebar").set_active(self.decoration)
        self.cancalEvent = False
        self.opacity = float(conf.GetOption("opacity").replace("%","")) / 100
        if self.opacity < 0.1:
            self.opacity = 0.1
        # self.mainWindow.set_opacity(self.opacity)
        # self.schedule.set_opacity(self.opacity)
        self.mainWindow.set_decorated(self.decoration)
        self.mainWindow.move(int(xpos), int(ypos))
        now = date.today()
        self.month = now.month
        self.year = now.year
        #壁紙一覧を作成
        if os.path.isdir(WALLPAPER_PATH) == False:
            WALLPAPER_PATH = "/usr/share/backgrounds"
        for base, path, imPath in os.walk(WALLPAPER_PATH+"/"):
            for img in imPath:
                limg = img.lower()
                if limg.find("jpg") > 0 or limg.find("png") > 0 or limg.find("jpeg") > 0:
                    if base[-1] != '/' :
                        self.wallpaper_list.append(base+"/"+img)
                    else:
                        self.wallpaper_list.append(base+img)
        self.changeWallPaper()
        self.set_style()
        self.makeCalendar(now.year, now.month)
        # self.updateWindowMask()
        self.mainWindow.show_all()
        # 60分毎にカレンダーを更新する
        self.timeout = GLib.timeout_add_seconds(int(60*60),self.timeout_callback,self)
        # 10分毎に壁紙を更新する
        # self.timeoutMask = GLib.timeout_add_seconds(int(10*60),self.timeoutChangeWallpaper_callback,self)

    def changeWallPaper(self):
        '''
        壁紙切り替え
        一度使用した壁紙が表示されないようにフラグ管理を行っている
        '''
        self.wlist = self.wallpaper_list
        if len(self.use_wallpaper_list) > 0:
            chkSet = set(self.use_wallpaper_list)
            self.wlist = [x for x in self.wallpaper_list if x not in chkSet]
            if len(self.wlist) == 0:
                self.use_wallpaper_list = []
                self.wlist = self.wallpaper_list
        self.sw = random.randint(0,len(self.wlist)-1)
        self.use_wallpaper_list.append(self.wlist[self.sw])
        self._saveConf()

    def timeout_callback(self,event):
        """タイムアウト時カレンダー情報更新
        15分ごとのタイムアウトでカレンダーに設定されているイベントを更新

        Returns:
            [type] -- [description]
        """
        self.makeCalendar(self.year, self.month)
        return True

    def timeoutChangeWallpaper_callback(self,event):
        self.changeWallPaper()
        self.set_style()
        # self.makeCalendar(self.year, self.month)
        return True

    def updateWindowMask(self):
        surface = cairo.ImageSurface(cairo.Format.ARGB32, self.w, self.h)
        ctx = cairo.Context(surface)
        ctx.set_source_rgba (1.0, 1.0, 1.0, 0.0)
        ctx.set_operator (cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator (cairo.OPERATOR_OVER)
        ctx.set_source_rgba(1.0,1.0,1.0)
        ctx.set_line_width(1)
        pix = 0
        for y in range(0, self.h, 3):
            for x in range(0, self.w, 3):
                ctx.move_to(x, y)
                ctx.line_to(x+2, y+2)
                ctx.stroke()
        surface.write_to_png("temp.png")
        region = Gdk.cairo_region_create_from_surface(surface)
        self.mainWindow.shape_combine_region(region)

    def on_draw(self, widget, event, userdata=None):
        cr = Gdk.cairo_create(widget.get_window())

        if self.supports_alpha:
            # print("setting transparent window")
            r = self.bgColor.red / 65536
            g = self.bgColor.green / 65536
            b = self.bgColor.blue / 65536
            cr.set_source_rgba(r,g,b, self.opacity)
        else:
            # print("setting opaque window")
            cr.set_source_rgb(1.0, 1.0, 1.0)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        return

    def makeCalendar(self,year,month):
        '''カレンダー生成
        Arguments:
            year {[int]} -- [カレンダーの年]
            month {[int]} -- [カレンダーの月]
        '''
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
                    self.days[row][col].set_tooltip_text(None) #ツールチップ初期化
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
        """カレンダー属性初期化
        """
        for row in range(6):
            for col in range(7):
                self.days[row][col].set_has_tooltip(False)
                css_context = self.days[row][col].get_style_context()
                css_context.remove_class("today")
                css_context.remove_class("holiday")
                css_context.remove_class("prev_month")
                css_context.remove_class("next_month")
                css_context.remove_class("selected")
                css_context.remove_class("marked")

    def findDayLabel(self, day):
        """指定日のカレンダーラベルコントロールの取得
        Arguments:
            day {[type]} -- [description]

        Returns:
            [Gtk.Label] -- [指定日のラベルコントロール]
        """
        for row in range(6):
            for col in range(7):
                css_context = self.days[row][col].get_style_context()
                if css_context.has_class("prev_month") == False and css_context.has_class("next_month") == False:
                    if int(self.days[row][col].get_text()) == day:
                        return self.days[row][col]
        return None

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip):
        """ツールチップ表示コールバック
        Arguments:
            widget {[type]} -- [description]
            x {[type]} -- [description]
            y {[type]} -- [description]
            keyboard_mode {[type]} -- [description]
            tooltip {[type]} -- [description]

        Returns:
            [bool] -- [True：表示/False：非表示]]
        """
        text = widget.get_tooltip_text()
        tooltip.set_text(text)
        return True

    def setHoliday(self, day, text):
        """祝日設定
        Arguments:
            day {[type]} -- [description]
            text {[type]} -- [description]
        """
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        css_context.add_class("holiday")
        day.set_has_tooltip(True)
        day.set_tooltip_text(text)
        day.connect("query-tooltip", self.tooltip_callback)


    def setMarked(self, day, text):
        """マーク指定
        Arguments:
            day {[type]} -- [description]
            text {[type]} -- [description]
        """
        day = self.findDayLabel(day)
        css_context = day.get_style_context()
        if css_context.has_class("marked"):
            tooltip = day.get_tooltip_text()
            tooltip += "\n" + text
            day.set_tooltip_text(tooltip)
        else:
            css_context.add_class("marked")
            day.set_has_tooltip(True)
            day.set_tooltip_text(text)
            day.connect("query-tooltip", self.tooltip_callback)

    def on_evMonthDown_button_release_event(self, wdget, event):
        """前月ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        prevdate = date(self.year,self.month,1) - timedelta(days=1)
        self.month = prevdate.month
        self.year = prevdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evMonthUp_button_release_event(self, wdget, event):
        """次月ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        firstWeek, lastday = calendar.monthrange(self.year, self.month)
        nextdate = date(self.year,self.month,lastday) + timedelta(days=1)
        self.month = nextdate.month
        self.year = nextdate.year
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearDonw_button_release_event(self, wdget, event):
        """前年ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.year -= 1
        self.makeCalendar(self.year, self.month)
        return

    def on_evYearUp_button_release_event(self, wdget, event):
        """次年ボタンクリックイベント
        Arguments:
            wdget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.year += 1
        self.makeCalendar(self.year, self.month)
        return

    def on_day_button_press_event(self, widget, event):
        """日付ラベルクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        day = widget.get_child()
        if day != None:
            css_context = day.get_style_context()
            if css_context.has_class("prev_month"):
                self.on_evMonthDown_button_release_event(widget, event)
            elif css_context.has_class("next_month"):
                self.on_evMonthUp_button_release_event(widget, event)
            else:
                if event.type == Gdk.EventType.BUTTON_PRESS  and event.button == 2:
                    # ホイールクリック
                    self.deleteEvent(day)
                elif event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS  and event.button == 1:
                    # 左ダブルクリック
                    self.addEvent(day)
        return

    def deleteEvent(self, day):
        """イベント削除ダイアログを表示
        指定日のイベントを削除するダイアログを表示

        Arguments:
            day {[type]} -- [description]
        """
        tooltip = day.get_tooltip_text()
        if tooltip != None and len(tooltip) > 0:
            event = tooltip.split("\n")
            deleteDialog  = Gtk.Dialog(parent = self.mainWindow, title = "予定の削除")
            deleteDialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            deleteDialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            lbl = Gtk.Label("削除する予定をチェック")
            deleteDialog.vbox.pack_start(lbl, False, False, 0)
            for ev in event:
                cb = Gtk.CheckButton(label = ev)
                deleteDialog.vbox.pack_start(cb, False, False, 0)
            deleteDialog.show_all()
            if deleteDialog.run() == Gtk.ResponseType.OK:
                for cb in deleteDialog.vbox.get_children():
                    if type(cb) == gi.repository.Gtk.CheckButton:
                        if cb.props.active:
                            delDate = date(self.year, self.month, int(day.get_text()))
                            cmd = GCAL_PATH + "gcalcli delete \"" + cb.props.label.split()[1] + "\" " + delDate.isoformat() + " --iamaexpert"
                            deleteDialog.hide()
                            while Gtk.events_pending():
                                Gtk.main_iteration()
                            self.res_cmd(cmd)
                            self.makeCalendar(self.year, self.month)
            deleteDialog.destroy()

    def on_wCalendar_button_press_event(self,widget,event):
        """メインウィンドウ上でのマウスボタンクリックイベント
        右クリックメニューの表示
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            #右クリック
            self.context_menu.popup(None, None, None,None, event.button, event.time)

    def on_miTitlebar_toggled(self, widget):
        """タイトルバーを表示メニューイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self.decoration = widget.get_active()
        self.mainWindow.set_decorated(self.decoration)
        return

    def on_evMonth_button_press_event(self, widget,event):
        """月ラベルマウスボタンクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(False)
        self.cmbYear.set_no_show_all(False)
        self.lblMonth.set_no_show_all(True)
        self.lblYear.set_no_show_all(True)
        self.lblMonth.hide()
        self.lblYear.hide()
        self.mainWindow.show_all()

    def on_evYear_button_press_event(self, widget,event):
        """年ラベルマウスボタンクリックイベント
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(False)
        self.cmbYear.set_no_show_all(False)
        self.lblMonth.set_no_show_all(True)
        self.lblYear.set_no_show_all(True)
        self.lblMonth.hide()
        self.lblYear.hide()
        self.mainWindow.show_all()

    def on_cmbMonth_changed(self, widget):
        """月コンボボックス選択イベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.lblMonth.show()
        self.lblYear.show()
        self.mainWindow.show_all()
        self.month = self.cmbMonth.get_active() + 1
        self.makeCalendar(self.year, self.month)
        return

    def on_cmbYear_changed(self, widget):
        """年コンボボックスイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.lblMonth.show()
        self.lblYear.show()
        self.mainWindow.show_all()
        self.year = int(self.cmbYear.get_active_text())
        self.makeCalendar(self.year, self.month)
        return

    def on_cmbMonth_popdown(self, widget):
        """月選択キャンセル
        ESCキーなどで月選択のキャンセル時のイベントハンドラ

        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.lblMonth.show()
        self.lblYear.show()
        self.mainWindow.show_all()

    def on_cmbYear_popdown(self, widget):
        """年選択キャンセル
        ESCキーなどで年選択のキャンセル時のイベントハンドラ

        Arguments:
            widget {[type]} -- [description]
        """
        self.cmbMonth.set_no_show_all(True)
        self.cmbYear.set_no_show_all(True)
        self.cmbMonth.hide()
        self.cmbYear.hide()
        self.lblMonth.show()
        self.lblYear.show()
        self.mainWindow.show_all()

    def _saveConf(self):
        """設定保存
        """
        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        global WALLPAPER_PATH
        conf = ConfigXML(False)
        (xpos, ypos) = self.mainWindow.get_position()
        (self.w, self.h) = self.mainWindow.get_size()
        if len(GCAL_PATH) > 0:
            GCAL_PATH = os.path.join(GCAL_PATH, '', '')
        conf.SetOption("x_pos",xpos)
        conf.SetOption("y_pos",ypos)
        conf.SetOption("width",self.w)
        conf.SetOption("height",self.h)
        conf.SetOption("opacity",str(self.opacity*100) + "%")
        conf.SetOption("decoration",str(self.decoration))
        conf.SetOption("gcal_path", GCAL_PATH)
        conf.SetOption("event_calendar", EVENT_CALENDAR)
        conf.SetOption("holiday_calendar", HOLIDAY_CALENDAR)
        conf.SetOption("bgColor", self.bgColor.to_string())
        conf.SetOption("mdColor", self.mdColor.to_string())
        conf.SetOption("tmColor",self.tmColor.to_string())
        conf.SetOption("textColor",self.textColor.to_string())
        conf.SetOption("wallpaper_path",WALLPAPER_PATH)
        conf.SetOption("use_wallpaper",str(self.use_wallpaper_list))
        conf.Write()

    def on_MainWindow_realize(self, widget):
        """メインウィンドウ表示イベント
        設定値を保存する
        Arguments:
            widget {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self._saveConf()
        return

    def on_wCalendar_focus_out_event(self, widget, event):
        """メインウィンドウフォーカスアウトイベント
        設定値を保存する
        Arguments:
            widget {[type]} -- [description]
            event {[type]} -- [description]
        """
        if self.cancalEvent == True:
            return
        self._saveConf()
        self.cancalEvent = False
        return

    def setEventDay(self):
        """gcalcliから取得したイベントをカレンダーに設定
        """
        if len(EVENT_CALENDAR) == 0:
            return
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + EVENT_CALENDAR + "\" --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        day = 0
        for sch in schedules:
            if len(sch) > 0 and sch != "No Events Found...":
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                self.setMarked(day.day, info[1] + " " + " ".join(info[4:]))

    def setEventDayList(self):
        """gcalcliから取得したイベント情報をTextViewに設定
        """
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday) +  timedelta(days=14)   # 月末から2週間後まで
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        dict.fromkeys(schedules)
        schedules = list(dict.fromkeys(schedules))
        self.txtBuffer.set_text("")
        textIter = self.txtBuffer.get_start_iter()
        scrollMark = 0
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                if datetime.today() > day:
                    scrollMark += 1
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.mdColor.to_string() + "'>" + "{:02d}/{:02d}".format(day.month,day.day) + "</span> ",-1)
                textIter = self.txtBuffer.get_end_iter()
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.tmColor.to_string() + "'>" + info[1]  + "</span> ",-1)
                textIter = self.txtBuffer.get_end_iter()
                self.txtBuffer.insert_markup(textIter, "<span foreground='" + self.textColor.to_string() + "'>" + " ".join(info[4:]) + "</span> " + "\n", -1)
                textIter = self.txtBuffer.get_end_iter()
        if scrollMark != 0:
            itr = self.txtBuffer.get_iter_at_line(scrollMark)
            mark = self.txtBuffer.create_mark(None, itr, True)
            ret = self.schedule.scroll_to_mark(mark, 0, False, 0, 0)

    def setHolidayList(self):
        """gcalcliから取得した祝日をカレンダーに設定
        """
        if len(HOLIDAY_CALENDAR) == 0:
            return
        montStart = date(self.year, self.month,1)
        _, lastday = calendar.monthrange(self.year, self.month)
        montFinish = date(self.year, self.month,lastday)
        schedules = self.res_cmd_no_lfeed(GCAL_PATH + "gcalcli " + "--calendar \"" + HOLIDAY_CALENDAR + "\" --nocolor agenda --tsv " + montStart.isoformat() + " " + montFinish.isoformat())
        for sch in schedules:
            if len(sch) > 0:
                info = sch.split("\t")
                day = datetime.strptime(info[0], "%Y-%m-%d")
                self.setHoliday(day.day, " ".join(info[4:]))

    def on_miExit_activate(self,widget):
        """終了メニューのイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        self._saveConf()
        Gtk.main_quit()

    def on_wCalendar_destroy(self,widget):
        """ウィンドウ破棄のイベントハンドラ
        Arguments:
            widget {[type]} -- [description]
        """
        Gtk.main_quit()

    def on_miSetting_activate(self, widget):
        """設定ダイアログを開く
        Arguments:
            widget {[type]} -- [description]
        """
        global GCAL_PATH
        global EVENT_CALENDAR
        global HOLIDAY_CALENDAR
        global WALLPAPER_PATH
        # 設定ダイアログ
        settingDialog = self.wMain.get_object ("dlgSetting")
        settingDialog.set_transient_for(self.mainWindow)
        btnFileChoose = self.wMain.get_object ("btnFileChoose")
        txtEventCalendar = self.wMain.get_object ("txtEventCalendar")
        txtHolidayCalendar = self.wMain.get_object ("txtHolidayCalendar")
        sclOpecity = self.wMain.get_object ("sclOpecity")
        btnBGColor = self.wMain.get_object ("btnBGColor")
        btnMDColor = self.wMain.get_object ("btnMDColor")
        btnTMColor = self.wMain.get_object ("btnTMColor")
        btnTextColor = self.wMain.get_object ("btnTextColor")
        # btnWallpaperChose = self.wMain.get_object("btnWallpaperChose")
        btnBGColor.set_color(self.bgColor)
        btnMDColor.set_color(self.mdColor)
        btnTMColor.set_color(self.tmColor)
        btnTextColor.set_color(self.textColor)
        btnFileChoose.set_current_folder(os.path.expanduser(GCAL_PATH))
        # btnWallpaperChose.set_current_folder(WALLPAPER_PATH)
        txtEventCalendar.set_text(EVENT_CALENDAR)
        txtHolidayCalendar.set_text(HOLIDAY_CALENDAR)
        sclOpecity.set_value(self.opacity * 100)
        settingDialog.show_all()
        if settingDialog.run() == Gtk.ResponseType.OK:
            GCAL_PATH = btnFileChoose.get_current_folder()
            EVENT_CALENDAR = txtEventCalendar.get_text()
            HOLIDAY_CALENDAR = txtHolidayCalendar.get_text()
            # WALLPAPER_PATH = btnWallpaperChose.get_current_folder()
            self.opacity = sclOpecity.get_value() / 100
            self.bgColor = btnBGColor.get_color()
            self.mdColor = btnMDColor.get_color()
            self.tmColor = btnTMColor.get_color()
            self.textColor = btnTextColor.get_color()
            # self.mainWindow.set_opacity(self.opacity)
            # self.schedule.set_opacity(self.opacity)
            self._saveConf()
            settingDialog.hide()
            while Gtk.events_pending():
                Gtk.main_iteration()
            self.setEventDayList()
        settingDialog.hide()

    def addEvent(self, day):
        """予定追加ダイアログを開く

        Arguments:
            day {[type]} -- [description]
        """
        # 予定追加ダイアログ
        scheduleDialog = self.wMain.get_object ("dlgAddSchedule")
        scheduleDialog.set_transient_for(self.mainWindow)
        lblAddDate = self.wMain.get_object ("lblAddDate")
        cmbHour = self.wMain.get_object ("cmbHour")
        cmbMin = self.wMain.get_object ("cmbMin")
        txtContent = self.wMain.get_object ("txtContent")
        dlSpan = self.wMain.get_object ("dlSpan")
        swAllDay = self.wMain.get_object ("swAllDay")
        txtBufferContents = self.wMain.get_object ("txtBufferContents")
        lblAddDate.set_text("{:04d}/{:02d}/{:02d}".format(self.year, self.month, int(day.get_text())))
        cmbHour.set_active(0)
        cmbMin.set_active(0)
        dlSpan.set_active(1)
        scheduleDialog.show_all()
        if scheduleDialog.run() == Gtk.ResponseType.OK:
            cmd = GCAL_PATH + "gcalcli " + "--calendar \"" + EVENT_CALENDAR + "\" add " \
                "--title \"" + txtContent.get_text() + "\" " + \
                "--noprompt "
            start_iter = txtBufferContents.get_start_iter()
            end_iter = txtBufferContents.get_end_iter()
            text = txtBufferContents.get_text(start_iter, end_iter, False)
            if len(text) > 0:
                cmd += "--description \"" + text + "\" "
            if swAllDay.get_active() > 0:
                cmd += "--allday "
            else:
                cmd += "--when \"" + lblAddDate.get_text() + " " + cmbHour.get_active_text() + ":" + cmbMin.get_active_text() +"\" " + \
                "--duration " + str(int(float(dlSpan.get_active_text()) * 60))
            scheduleDialog.hide()
            while Gtk.events_pending():
                Gtk.main_iteration()
            print(cmd)
            self.res_cmd(cmd)
            self.makeCalendar(self.year, self.month)
        scheduleDialog.hide()

    def res_cmd(self, cmd):
        """cmdで指定されたコマンドをサブプロセスで実行し、結果をひとつの文字列で返却する
        Arguments:
            cmd {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).communicate()[0].decode("utf-8", "ignore")

    def res_cmd_lfeed(self, cmd):
        """cmdで指定されたコマンドをサブプロセスで実行し、結果をリストで返す（末尾改行）
        Arguments:
            cmd {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            shell=True).stdout.readlines()

    def res_cmd_no_lfeed(self, cmd):
        """cmdで指定されたコマンドをサブプロセスで実行し、結果をリストで返す（末尾改行なし）
        Arguments:
            cmd {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        return [bytes(x).decode("utf-8", "ignore").rstrip("\n") for x in self.res_cmd_lfeed(cmd)]

    def set_style(self):
        """Change Gtk+ Style
        """
        provider = Gtk.CssProvider()
        with open(join(WHERE_AM_I, 'gcalcal.css')) as cssFile:
            css = cssFile.read()
            css = css.replace("###WALLPAPER###",self.wlist[self.sw])
        # Demo CSS kindly provided by Numix project
        provider.load_from_data(css.encode())
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
