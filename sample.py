#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo


supports_alpha = False


def screen_changed(widget, old_screen, userdata=None):
    global supports_alpha

    screen = widget.get_screen()
    visual = screen.get_rgba_visual()

    if visual is None:
        print("Your screen does not support alpha channels!")
        visual = screen.get_system_visual()
        supports_alpha = False
    else:
        print("Your screen supports alpha channels!")
        supports_alpha = True

    widget.set_visual(visual)


def expose_draw(widget, event, userdata=None):
    global supports_alpha

    cr = Gdk.cairo_create(widget.get_window())

    if supports_alpha:
        print("setting transparent window")
        cr.set_source_rgba(1.0, 0.5, 1.0, 0.8)
    else:
        print("setting opaque window")
        cr.set_source_rgb(1.0, 1.0, 1.0)

    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()

    return False


def clicked(window, event, userdata=None):
    # toggle window manager frames
    window.set_decorated(not window.get_decorated())


if __name__ == "__main__":
    window = Gtk.Window()
    window.set_position(Gtk.WindowPosition.CENTER)
    window.set_default_size(400, 400)
    window.set_title("Alpha Demo")
    window.connect("delete-event", Gtk.main_quit)

    window.set_app_paintable(True)

    window.connect("draw", expose_draw)
    window.connect("screen-changed", screen_changed)

    window.set_decorated(False)
    window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    window.connect("button-press-event", clicked)

    fixed_container = Gtk.Fixed()
    window.add(fixed_container)
    button = Gtk.Button.new_with_label("button1")
    button.set_size_request(100, 100)
    fixed_container.add(button)

    screen_changed(window, None, None)

    window.show_all()
    Gtk.main()
