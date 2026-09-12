"""Tests for the non-TUI logic of eazykill.

These exercise the pure/independent functions without needing a GUI or a
terminal: the `lsappinfo` parser, relative-time formatting, PID liveness,
and the graceful-quit verification loop.

Run from the project root:

    python3 -m unittest discover -s tests
"""

import importlib.machinery
import pathlib
import subprocess
import unittest
from datetime import datetime, timedelta
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'eazykill'
ea = importlib.machinery.SourceFileLoader('eazykill', str(SCRIPT)).load_module()


def ts(dt):
    return dt.strftime('%Y/%m/%d %H:%M:%S')


LSAPPINFO_SAMPLE = """\
 1) "Firefox" ASN:0x0-0xb53c531: 
    bundleID="org.mozilla.firefox"
    bundle path="/Applications/Firefox.app"
    executable path="/Applications/Firefox.app/Contents/MacOS/firefox"
    pid = 69255 type="Foreground" flavor=3 Version="15526.9.3" fileType="APPL" creator="MOZB" Arch=ARM64 
    parentASN=ASN:0x1-0x10e7e: 
    launch time =  2026/09/05 15:14:18 ( 7 days, 17 minutes, 56.5933 seconds ago )
    checkin time = 2026/09/05 15:14:18 ( 7 days, 17 minutes, 56.436 seconds ago )
    launch to checkin time: 0.157287 seconds

 2) "FirefoxCP Web Content" ASN:0x0-0xe5fd5ef: 
    bundleID="org.mozilla.plugincontainer"
    bundle path="/Applications/Firefox.app/Contents/MacOS/plugin-container.app"
    executable path="/Applications/Firefox.app/Contents/MacOS/plugin-container.app/Contents/MacOS/plugin-container"
    pid = 8009 !cgsConnection !signalled type="BackgroundOnly" flavor=2 Version="1.0" fileType="APPL" creator="????" Arch=ARM64 sandboxed 

 3) "Dock" ASN:0x0-0x20020: 
    bundleID="com.apple.dock"
    pid = 800 type="UIElement" flavor=3 Version="1.0" fileType="APPL" Arch=ARM64 

 4) "Finder" ASN:0x0-0x1c01c: 
    bundleID="com.apple.finder"
    bundle path="/System/Library/CoreServices/Finder.app"
    pid = 753 type="Foreground" flavor=3 Version="1732.6.4.2" fileType="FNDR" creator="MACS" Arch=ARM64 
    checkin time = 2026/08/03 02:37:58 ( 40 days, 12 hours, 56 minutes, 49.6534 seconds ago )

 5) "Calculator" ASN:0x0-0xe7e57d7: (in front) 
    bundleID="com.apple.calculator"
    bundle path="/System/Applications/Calculator.app"
    executable path="/System/Applications/Calculator.app/Contents/MacOS/Calculator"
    pid = 42022 type="Foreground" flavor=3 Version="224" fileType="APPL" Arch=ARM64 sandboxed 
    parentASN=ASN:0x1-0xa424: 
    launch time =  2 seconds ago, 2026/09/12 15:35:22 ( 2.09586 seconds ago )
"""


class TestRelative(unittest.TestCase):
    def test_days(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(days=2))),
                         '2 days ago')

    def test_singular_day(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(days=1))),
                         '1 day ago')

    def test_hours(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(hours=3))),
                         '3 hours ago')

    def test_singular_hour(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(hours=1))),
                         '1 hour ago')

    def test_minutes(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(minutes=45))),
                         '45 minutes ago')

    def test_just_now(self):
        self.assertEqual(ea.relative(ts(datetime.now() - timedelta(seconds=5))),
                         'just now')


class TestParse(unittest.TestCase):
    def test_captures_all_entry_types(self):
        types = {a['name']: a['type'] for a in ea.parse_lsappinfo(LSAPPINFO_SAMPLE)}
        self.assertEqual(types['Firefox'], 'Foreground')
        self.assertEqual(types['FirefoxCP Web Content'], 'BackgroundOnly')
        self.assertEqual(types['Dock'], 'UIElement')

    def test_foreground_fields(self):
        ff = next(a for a in ea.parse_lsappinfo(LSAPPINFO_SAMPLE)
                  if a['name'] == 'Firefox')
        self.assertEqual(ff['pid'], 69255)
        self.assertEqual(ff['bundle'], 'org.mozilla.firefox')
        self.assertEqual(ff['launch'], '2026/09/05 15:14:18')

    def test_checkin_time_fallback(self):
        finder = next(a for a in ea.parse_lsappinfo(LSAPPINFO_SAMPLE)
                      if a['name'] == 'Finder')
        self.assertEqual(finder['launch'], '2026/08/03 02:37:58')

    def test_recent_launch_format(self):
        calc = next(a for a in ea.parse_lsappinfo(LSAPPINFO_SAMPLE)
                    if a['name'] == 'Calculator')
        self.assertEqual(calc['launch'], '2026/09/12 15:35:22')


class TestListApps(unittest.TestCase):
    def test_filters_foreground_and_adds_ago(self):
        fake = mock.Mock()
        fake.stdout = LSAPPINFO_SAMPLE
        with mock.patch.object(ea.subprocess, 'run', return_value=fake):
            apps = ea.list_apps()
        self.assertEqual([a['name'] for a in apps],
                         ['Firefox', 'Finder', 'Calculator'])
        self.assertTrue(all('ago' in a for a in apps))


class TestPidAlive(unittest.TestCase):
    def test_live_then_dead(self):
        p = subprocess.Popen(['sleep', '100'])
        self.assertTrue(ea.pid_alive(p.pid))
        p.terminate()
        p.wait()
        self.assertFalse(ea.pid_alive(p.pid))


class TestQuitVerify(unittest.TestCase):
    def test_success_when_process_gone(self):
        p = subprocess.Popen(['sleep', '100'])
        pid = p.pid
        p.terminate()
        p.wait()
        with mock.patch.object(ea, 'quit_app', return_value=(True, '')):
            result = {}
            ea._do_quit({'name': 'x', 'pid': pid, 'bundle': 'x'}, result)
        self.assertTrue(result['ok'])
        self.assertEqual(result['err'], '')

    def test_failure_when_still_alive(self):
        p = subprocess.Popen(['sleep', '100'])
        try:
            with mock.patch.object(ea, 'quit_app', return_value=(True, '')), \
                 mock.patch.object(ea.time, 'sleep', return_value=None):
                result = {}
                ea._do_quit({'name': 'x', 'pid': p.pid, 'bundle': 'x'}, result)
        finally:
            p.terminate()
            p.wait()
        self.assertFalse(result['ok'])
        self.assertIn('force kill', result['err'])


if __name__ == '__main__':
    unittest.main()
