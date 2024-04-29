from rzctl_nt import (
    ntdll,
    kernel32,
    find_sym_link,
    INVALID_HANDLE_VALUE,
    FILE_SHARE_READ,
    FILE_SHARE_WRITE,
    OPEN_EXISTING,
    Structure,
    c_int32,
    c_ulong,
    pointer,
    sizeof,
    byref,
    BOOL,
)


def enum(**enums):
    return type("Enum", (), enums)


MOUSE_CLICK = enum(
    LEFT_DOWN=1,
    LEFT_UP=2,
    RIGHT_DOWN=4,
    RIGHT_UP=8,
    SCROLL_CLICK_DOWN=16,
    SCROLL_CLICK_UP=32,
    BACK_DOWN=64,
    BACK_UP=128,
    FOWARD_DOWN=256,
    FOWARD_UP=512,
    SCROLL_DOWN=4287104000,
    SCROLL_UP=7865344,
)

KEYBOARD_INPUT_TYPE = enum(KEYBOARD_DOWN=0, KEYBOARD_UP=1)


class RZCONTROL_IOCTL_STRUCT(Structure):
    _fields_ = [
        ("unk0", c_int32),
        ("unk1", c_int32),
        ("max_val_or_scan_code", c_int32),
        ("click_mask", c_int32),
        ("unk3", c_int32),
        ("x", c_int32),
        ("y", c_int32),
        ("unk4", c_int32),
    ]


IOCTL_MOUSE = 0x88883020
MAX_VAL = 65536
RZCONTROL_MOUSE = 2
RZCONTROL_KEYBOARD = 1


class RZCONTROL:

    hDevice = INVALID_HANDLE_VALUE

    def __init__(self):
        pass

    def init(self):
        if RZCONTROL.hDevice != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(hDevice)
        found, name = find_sym_link("\\GLOBAL??", "RZCONTROL")
        if not found:
            return False
        sym_link = "\\\\?\\" + name
        RZCONTROL.hDevice = kernel32.CreateFileW(
            sym_link, 0, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, 0, 0
        )
        return RZCONTROL.hDevice != INVALID_HANDLE_VALUE

    def impl_mouse_ioctl(self, ioctl):
        if ioctl:
            p_ioctl = pointer(ioctl)
            junk = c_ulong()
            bResult = kernel32.DeviceIoControl(
                RZCONTROL.hDevice,
                IOCTL_MOUSE,
                p_ioctl,
                sizeof(RZCONTROL_IOCTL_STRUCT),
                0,
                0,
                byref(junk),
                0,
            )
            if not bResult:
                self.init()

    def mouse_move(self, x, y, from_start_point):
        """if going from point, x and y will be the offset from current mouse position
               otherwise it will be a number in range of 1 to 65536, where 1, 1 is top left of screen
               if using multiple monitors the input values remain the same, but outcome different, i just don't recommend bothering with this bs
               note: x and/or y can not be 0 unless going from start point

        Args:
            x (int)
            y (int)
            from_start_point (bool)
        """
        max_val = 0
        if not from_start_point:
            max_val = MAX_VAL
            if x < 1:
                x = 1
            if x > max_val:
                x = max_val
            if y < 1:
                y = 1
            if y > max_val:
                y = max_val
        mm = RZCONTROL_IOCTL_STRUCT(0, RZCONTROL_MOUSE, max_val, 0, 0, x, y, 0)
        self.impl_mouse_ioctl(mm)

    def mouse_click(self, click_mask):
        """
        Args:
            click_mask (MOUSE_CLICK):
        """
        mm = RZCONTROL_IOCTL_STRUCT(
            0,
            RZCONTROL_MOUSE,
            0,
            click_mask,
            0,
            0,
            0,
            0,
        )
        self.impl_mouse_ioctl(mm)

    def keyboard_input(self, scan_code, up_down):
        """
        Args:
            scan_code (short): https://www.millisecond.com/support/docs/current/html/language/scancodes.htm
            up_down (KEYBOARD_INPUT_TYPE): _description_
        """
        mm = RZCONTROL_IOCTL_STRUCT(
            0,
            RZCONTROL_KEYBOARD,
            (int(scan_code) << 16),
            up_down,
            0,
            0,
            0,
            0,
        )
        self.impl_mouse_ioctl(mm)
