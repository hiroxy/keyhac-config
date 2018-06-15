import os.path
import re
import sys
import time
import ckit
from ckit.ckit_const import *
import accessibility

from keyhac import *
from keyhac_hook import *
from keyhac_keymap import *

def configure(keymap):
    keymap.editor = "Emacs"

    apps_not_being_emacs_key = [
        "org.gnu.Emacs",
        "com.googlecode.iterm2",
        "com.apple.Terminal",
        "org.virtualbox.app.VirtualBoxVM",
        "com.microsoft.rdc.mac",
        "com.microsoft.VSCode",
    ]

    is_japanese_keyboard = False
    side_of_ctrl_key = "L"
    side_of_alt_key = "L"
    use_esc_as_meta = False

    class Fakeymacs:
        pass

    fakeymacs = Fakeymacs()
    fakeymacs.is_digit_argument = False
    fakeymacs.is_marked = False
    fakeymacs.is_playing_keyboardmacro = False
    fakeymacs.is_searching = False
    fakeymacs.is_undo_mode = True
    fakeymacs.is_universal_argument = False
    fakeymacs.last_window = 0
    fakeymacs.repeat_counter = 1

    def is_emacs_target(window):
        if window != fakeymacs.last_window:
            fakeymacs.last_window = window
        if ckit.getApplicationNameByPid(window.pid) in apps_not_being_emacs_key:
            fakeymacs.keybind = "not_emacs"
            return False
        fakeymacs.keybind = "emacs"
        return True

    keymap_emacs = keymap.defineWindowKeymap(check_func=is_emacs_target)

    # Global keymap which affects any windows
    keymap_global = keymap.defineWindowKeymap()

    ##################################################
    ## File
    ##################################################
    def find_file():
        self_insert_command("Cmd-o")()

    def save_buffer():
        self_insert_command("Cmd-s")()

    ##################################################
    ## Cursor
    ##################################################
    def backward_char():
        self_insert_command("Left")()

    def forward_char():
        self_insert_command("Right")()

    def backward_word():
        self_insert_command("Alt-Left")()

    def forward_word():
        self_insert_command("Alt-Right")()

    def previous_line():
        self_insert_command("Up")()

    def next_line():
        self_insert_command("Down")()

    def move_beginning_of_line():
#        self_insert_command("Ctrl-Left")()
        self_insert_command("Cmd-Left")()

    def move_end_of_line():
#        self_insert_command("Ctrl-Right")()
        self_insert_command("Cmd-Right")()

    def beginning_of_buffer():
        self_insert_command("Cmd-Up")()

    def end_of_buffer():
        self_insert_command("Cmd-Down")()

    def scroll_up():
        self_insert_command("Alt-PageUp")()

    def scroll_down():
        self_insert_command("Alt-PageDown")()


    ##################################################
    ## Cut / Copy / Delete / Undo
    ##################################################

    def delete_backward_char():
        self_insert_command("Back")()

    def delete_char():
        self_insert_command("Delete")()

    def backward_kill_word(repeat=1):
        fakeymacs.is_marked = True
        def move_beginning_of_region():
            for i in range(repeat):
                backward_word()
        mark(move_beginning_of_region)()
        delay()
        kill_region()

    def kill_word(repeat=1):
        fakeymacs.is_marked = True
        def move_end_of_region():
            for i in range(repeat):
                forward_word()
        mark(move_end_of_region)()
        delay()
        kill_region()

    def kill_line(repeat=1):
        fakeymacs.is_marked = True
        if repeat == 1:
            mark(move_end_of_line)()
            delay()
            self_insert_command("Cmd-c", "Delete")()
        else:
            def move_end_of_region():
                for i in range(repeat - 1):
                    next_line()
                move_end_of_line()
                forward_char()
            mark(move_end_of_region)()
            delay()
            kill_region()

    def kill_region():
        self_insert_command("Cmd-x")()

    def kill_ring_save():
        self_insert_command("Cmd-c")()

    def yank():
        self_insert_command("Cmd-v")()

    def undo():
        if fakeymacs.is_undo_mode:
            self_insert_command("Cmd-z")()
        else:
            self_insert_command("Cmd-y")()

    def set_mark_command():
        fakeymacs.is_marked = not fakeymacs.is_marked

    def mark_whole_buffer():
        self_insert_command("Cmd-a")()

    def open_line():
        self_insert_command("Enter", "Up", "End")()

    ##################################################
    ## Find / Replace
    ##################################################

    def isearch(direction):
        if fakeymacs.is_searching:
            self_insert_command({"backward": "Cmd-S-g", "forward": "Cmd-g"}[direction])()
        else:
            self_insert_command("Cmd-f")()
            keymap_emacs.is_searching = True

    def isearch_backward():
        isearch("backward")

    def isearch_forward():
        isearch("forward")

    def query_replace():
        self_insert_command("Cmd-f", "A-Cmd-F")()

    ##################################################
    ## Buffer / Windows
    ##################################################

    def kill_emacs():
        self_insert_command("Cmd-q")()

    def universal_argument():
        if fakeymacs.is_universal_argument:
            if fakeymacs.is_digit_argument == True:
                fakeymacs.is_universal_argument = False
            else:
                fakeymacs.repeat_counter *= 4
        else:
            fakeymacs.is_universal_argument = True
            fakeymacs.repeat_counter *= 4

    def digit_argument(number):
        if fakeymacs.is_digit_argument:
            fakeymacs.repeat_counter = fakeymacs.repeat_counter * 10 + number
        else:
            fakeymacs.is_digit_argument = True
            fakeymacs.repeat_counter = number

    ##################################################
    ## Misc
    ##################################################
    def tab():
        self_insert_command("Tab")()

    def keyboard_quit():
        self_insert_command("Esc")()
        fakeymacs.is_undo_mode = not fakeymacs.is_undo_mode

    ##################################################
    ## Common Functions
    ##################################################
    def delay(sec=0.02):
        time.sleep(sec)

    def addSideModifier(key):
        if key.startswith("Ctrl-"):
            key = key.replace("Ctrl-", side_of_ctrl_key + "Ctrl-")
        if key.startswith("Alt-"):
            key = key.replace("A-", side_of_alt_key + "A-")
        return key

    def kbd(keys):
        if len(keys) == 0:
            return []

        keys_lists = []
        keys_list = [keys.split()]
        for key in keys_list:
            # TODO: Do we need to check "C-M-"?
            key[0] = key[0].replace("C-", side_of_ctrl_key + "Ctrl-", 1)
            key[0] = key[0].replace("A-", side_of_ctrl_key + "Alt-", 1)
            key[0] = key[0].replace("S-", "Shift-", 1)
            if key[0].startswith("M-"):
                k = key[0].replace("M-", "", 1)
                key[0] = side_of_alt_key + "Alt-" + k
                keys_lists.append([side_of_ctrl_key + "Ctrl-OpenBracket", k])
                if use_esc_as_meta:
                    keys_lists.append(["Esc", k])

            if len(key) == 2:
                key[1] = key[1].replace("C-", side_of_ctrl_key + "Ctrl-", 1)
                key[1] = key[1].replace("S-", "Shift-", 1)

            keys_lists.append(key)

        return keys_lists

    def define_key(keymap, keys, command):
        for keys_list in kbd(keys):
            if len(keys_list) == 1:
                keymap[keys_list[0]] = command
            else:
                keymap[keys_list[0]][keys_list[1]] = command

    def self_insert_command(*keys):
        return keymap.InputKeyCommand(*list(map(addSideModifier, keys)))

    def self_insert_command2(*keys):
        return self_insert_command(*keys)

    def digit(number):
        def _func():
            if fakeymacs.is_universal_argument:
                digit_argument(number)
            else:
                reset_undo(reset_counter(reset_mark(repeat(self_insert_command2(str(number))))))()
        return _func

    def digit2(number):
        def _func():
            fakeymacs.is_universal_argument = True
            digit_argument(number)
        return _func

    def mark(func):
        def _func():
            if fakeymacs.is_marked:
                # If D-Shift is used, it is cancelled when M-< or M-> is used
                self_insert_command("D-LShift", "D-RShift")()
                delay()
                func()
                self_insert_command("U-LShift", "U-RShift")()
            else:
                func()
        return _func

    def reset_mark(func):
        def _func():
            func()
            fakeymacs.is_marked = False
        return _func

    def reset_counter(func):
        def _func():
            func()
            fakeymacs.is_universal_argument = False
            fakeymacs.is_digit_argument = False
            fakeymacs.repeat_counter = 1
        return _func

    def reset_undo(func):
        def _func():
            func()
            fakeymacs.is_undo_mode = True
        return _func

    def reset_search(func):
        def _func():
            func()
            fakeymacs.is_searching = False
        return _func

    def repeat(func):
        def _func():
            # 以下の２行は、キーボードマクロの繰り返し実行の際に必要な設定
            repeat_counter = fakeymacs.repeat_counter
            fakeymacs.repeat_counter = 1
            for i in range(repeat_counter):
                func()
        return _func

    def repeat2(func):
        def _func():
            if fakeymacs.is_marked:
                fakeymacs.repeat_counter = 1
            repeat(func)()
        return _func

    def repeat3(func):
        def _func():
            func(fakeymacs.repeat_counter)
        return _func

    ## define multi stroke keys
    define_key(keymap_emacs, "C-x", keymap.defineMultiStrokeKeymap("Ctrl-x"))
    define_key(keymap_emacs, "C-OpenBracket", keymap.defineMultiStrokeKeymap("Ctrl-OpenBracket"))
    if use_esc_as_meta:
        define_key(keymap_emacs, "Esc", keymap.defineMultiStrokeKeymap("Esc"))

    ## define numeric key
    for key in range(10):
        k = str(key)
        define_key(keymap_emacs,        k, digit(key))
        define_key(keymap_emacs, "C-" + k, digit2(key))
        define_key(keymap_emacs, "M-" + k, digit2(key))
        define_key(keymap_emacs, "S-" + k, reset_undo(reset_counter(reset_mark(repeat(self_insert_command2("S-" + k))))))

    ## file operations
    define_key(keymap_emacs, "C-x C-f", reset_search(reset_undo(reset_counter(reset_mark(find_file)))))
    define_key(keymap_emacs, "C-x C-s", reset_search(reset_undo(reset_counter(reset_mark(save_buffer)))))

    ## move cursor
    define_key(keymap_emacs, "C-b",        reset_search(reset_undo(reset_counter(mark(repeat(backward_char))))))
    define_key(keymap_emacs, "C-f",        reset_search(reset_undo(reset_counter(mark(repeat(forward_char))))))
    define_key(keymap_emacs, "M-b",        reset_search(reset_undo(reset_counter(mark(repeat(backward_word))))))
    define_key(keymap_emacs, "M-f",        reset_search(reset_undo(reset_counter(mark(repeat(forward_word))))))
    define_key(keymap_emacs, "C-p",        reset_search(reset_undo(reset_counter(mark(repeat(previous_line))))))
    define_key(keymap_emacs, "C-n",        reset_search(reset_undo(reset_counter(mark(repeat(next_line))))))
    define_key(keymap_emacs, "M-v",        reset_search(reset_undo(reset_counter(mark(scroll_up)))))
    define_key(keymap_emacs, "C-v",        reset_search(reset_undo(reset_counter(mark(scroll_down)))))
    define_key(keymap_emacs, "C-a",        reset_search(reset_undo(reset_counter(mark(move_beginning_of_line)))))
    define_key(keymap_emacs, "C-e",        reset_search(reset_undo(reset_counter(mark(move_end_of_line)))))
    define_key(keymap_emacs, "M-S-Comma",  reset_search(reset_undo(reset_counter(mark(beginning_of_buffer)))))
    define_key(keymap_emacs, "M-S-Period", reset_search(reset_undo(reset_counter(mark(end_of_buffer)))))

    define_key(keymap_emacs, "Left",     reset_search(reset_undo(reset_counter(mark(repeat(backward_char))))))
    define_key(keymap_emacs, "Right",    reset_search(reset_undo(reset_counter(mark(repeat(forward_char))))))
    define_key(keymap_emacs, "Up",       reset_search(reset_undo(reset_counter(mark(repeat(previous_line))))))
    define_key(keymap_emacs, "Down",     reset_search(reset_undo(reset_counter(mark(repeat(next_line))))))
    define_key(keymap_emacs, "PageUP",   reset_search(reset_undo(reset_counter(mark(scroll_up)))))
    define_key(keymap_emacs, "PageDown", reset_search(reset_undo(reset_counter(mark(scroll_down)))))
    define_key(keymap_emacs, "Home",     reset_search(reset_undo(reset_counter(mark(move_beginning_of_line)))))
    define_key(keymap_emacs, "End",      reset_search(reset_undo(reset_counter(mark(move_end_of_line)))))

    ## Cut, Copy, Delete and Undo
    if is_japanese_keyboard:
        define_key(keymap_emacs, "C-Atmark", reset_search(reset_undo(reset_counter(set_mark_command))))
    else:
        define_key(keymap_emacs, "C-S-2", reset_search(reset_undo(reset_counter(set_mark_command))))
    define_key(keymap_emacs, "C-Space",   reset_search(reset_undo(reset_counter(set_mark_command))))
    define_key(keymap_emacs, "C-x h",     reset_search(reset_undo(reset_counter(reset_mark(mark_whole_buffer)))))
    define_key(keymap_emacs, "Back",      reset_search(reset_undo(reset_counter(reset_mark(repeat2(delete_backward_char))))))
    define_key(keymap_emacs, "C-h",       reset_search(reset_undo(reset_counter(reset_mark(repeat2(delete_backward_char))))))
    define_key(keymap_emacs, "Delete",    reset_search(reset_undo(reset_counter(reset_mark(repeat2(delete_char))))))
    define_key(keymap_emacs, "C-d",       reset_search(reset_undo(reset_counter(reset_mark(repeat2(delete_char))))))
    define_key(keymap_emacs, "C-Back",    reset_search(reset_undo(reset_counter(reset_mark(repeat3(backward_kill_word))))))
    define_key(keymap_emacs, "M-Delete",  reset_search(reset_undo(reset_counter(reset_mark(repeat3(backward_kill_word))))))
    define_key(keymap_emacs, "C-Delete",  reset_search(reset_undo(reset_counter(reset_mark(repeat3(kill_word))))))
    define_key(keymap_emacs, "M-d",       reset_search(reset_undo(reset_counter(reset_mark(repeat3(kill_word))))))
    define_key(keymap_emacs, "C-k",       reset_search(reset_undo(reset_counter(reset_mark(repeat3(kill_line))))))
    define_key(keymap_emacs, "C-w",       reset_search(reset_undo(reset_counter(reset_mark(kill_region)))))
    define_key(keymap_emacs, "M-w",       reset_search(reset_undo(reset_counter(reset_mark(kill_ring_save)))))
    define_key(keymap_emacs, "C-y",       reset_search(reset_undo(reset_counter(reset_mark(repeat(yank))))))
    define_key(keymap_emacs, "C-Slash",   reset_search(reset_counter(reset_mark(undo))))
    define_key(keymap_emacs, "C-x u",     reset_search(reset_counter(reset_mark(undo))))
    if is_japanese_keyboard:
        define_key(keymap_emacs, "C-S-BackSlash", reset_search(reset_undo(reset_counter(reset_mark(undo)))))
    else:
        define_key(keymap_emacs, "C-S-Minus", reset_search(reset_undo(reset_counter(reset_mark(undo)))))

    ## Search, Replace
    define_key(keymap_emacs, "C-r",   reset_undo(reset_counter(reset_mark(isearch_backward))))
    define_key(keymap_emacs, "C-s",   reset_undo(reset_counter(reset_mark(isearch_forward))))
    define_key(keymap_emacs, "M-S-5", reset_search(reset_undo(reset_counter(reset_mark(query_replace)))))

    ## Misc
    define_key(keymap_emacs, "C-i",     reset_search(reset_counter(reset_mark(tab))))
    define_key(keymap_emacs, "C-g",     reset_search(reset_counter(reset_mark(keyboard_quit))))
    define_key(keymap_emacs, "C-x C-c", reset_search(reset_undo(reset_counter(reset_mark(kill_emacs)))))
    define_key(keymap_emacs, "C-u",     reset_undo(universal_argument))
