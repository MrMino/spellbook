"""Open the given file in the default $EDITOR, at a given line number."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

DEFAULTS = {
    "posix": "vi",
    "nt": "notepad",
}


def choose_editor() -> str | None:
    user_editor = os.getenv("EDITOR")

    if user_editor is not None:
        return user_editor

    return DEFAULTS.get(os.name, None)


def no_lineno(path: str, _: int) -> list[str]:
    return [path]


def vi_style_linemark(path: str, lineno: int) -> list[str]:
    return [path, f"+{lineno}"]


def emacsclient_linemark(path: str, lineno: int) -> list[str]:
    return [f"+{lineno}:0", path]


def notepad_plus_plus_n_opt(path: str, lineno: int) -> list[str]:
    return [path, f"-n{lineno}"]


def vscode_goto(path: str, lineno: int) -> list[str]:
    return ["--goto", f"{path}:{lineno}:0"]


def pycharm_line_opt(path: str, lineno: int) -> list[str]:
    return ["--line", str(lineno), path]


OPT_GENERATOR = {
    "vi": vi_style_linemark,
    "vim": vi_style_linemark,
    "nvim": vi_style_linemark,
    "nano": vi_style_linemark,
    "gedit": vi_style_linemark,
    "emacsclient": emacsclient_linemark,
    "code": vscode_goto,
    "notepad": no_lineno,
    "notepad++": notepad_plus_plus_n_opt,
    "pycharm64": pycharm_line_opt,
    "pycharm": pycharm_line_opt,
}


def call_tty_child(argv):
    subprocess.call(argv)


def call_detached(argv):
    if os.name == "nt":
        subprocess.Popen(
            argv,
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        subprocess.Popen(argv, start_new_session=True)


USES_TTY = {
    "vi": True,
    "vim": True,
    "nvim": True,
    "nano": True,
    "gedit": False,
    "emacsclient": True,
    "code": False,
    "notepad": False,
    "notepad++": False,
    "pycharm64": False,
    "pycharm": False,
}


def open_editor(path, lineno: int | None = None, editor: str | None = None) -> None:
    if editor is None:
        editor = choose_editor()

    if editor is None:
        raise RuntimeError("No 'editor' value given and no default available.")

    editor_name, _ = os.path.splitext(editor)
    if lineno is None:
        opts = [path]
    else:
        opt_generator = OPT_GENERATOR[editor_name]
        opts = opt_generator(path, lineno)

    exec_path = shutil.which(editor)
    assert isinstance(exec_path, str)

    argv = [exec_path] + opts
    call = call_tty_child if USES_TTY[editor_name] else call_detached

    call(argv)


if __name__ == "__main__":
    open_editor(sys.argv[1], int(sys.argv[2]))
