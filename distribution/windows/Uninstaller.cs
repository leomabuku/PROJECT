using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("TongaLang Uninstaller")]
[assembly: AssemblyCompany("Leo Mabuku")]
[assembly: AssemblyProduct("TongaLang")]
[assembly: AssemblyVersion("0.2.0.0")]
[assembly: AssemblyFileVersion("0.2.0.0")]

internal static class TongaLangUninstaller
{
    private const string AppName = "TongaLang";
    private const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\TongaLang";
    private static string TestRoot;

    private static void ConfigureTestRoot(string[] args)
    {
        for (int index = 0; index < args.Length - 1; index++)
        {
            if (args[index].Equals("--test-root", StringComparison.OrdinalIgnoreCase))
            {
                TestRoot = Path.GetFullPath(args[index + 1]);
                return;
            }
        }
    }

    private static string ValidatedInstallDirectory()
    {
        string actual = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory).TrimEnd(Path.DirectorySeparatorChar);
        string root = TestRoot ?? Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string expected = Path.GetFullPath(Path.Combine(root, "Programs", AppName)).TrimEnd(Path.DirectorySeparatorChar);
        if (!actual.Equals(expected, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Refusing to remove an unexpected folder: " + actual);
        return actual;
    }

    private static void RemoveShortcuts()
    {
        string menu = TestRoot == null
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), AppName)
            : Path.Combine(TestRoot, "StartMenu", AppName);
        foreach (string name in new[] { "TongaLang.lnk", "Uninstall TongaLang.lnk" })
        {
            string shortcut = Path.Combine(menu, name);
            if (File.Exists(shortcut)) File.Delete(shortcut);
        }
        if (Directory.Exists(menu) && Directory.GetFileSystemEntries(menu).Length == 0) Directory.Delete(menu);
        if (TestRoot == null)
        {
            string desktop = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "TongaLang.lnk");
            if (File.Exists(desktop)) File.Delete(desktop);
        }
    }

    private static void ScheduleRemoval(string target)
    {
        string safe = target.Replace("'", "''");
        string script = "Start-Sleep -Milliseconds 800; Remove-Item -LiteralPath '" + safe + "' -Recurse -Force";
        string encoded = Convert.ToBase64String(Encoding.Unicode.GetBytes(script));
        ProcessStartInfo info = new ProcessStartInfo("powershell.exe", "-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand " + encoded);
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        Process.Start(info);
    }

    private static void Uninstall()
    {
        string target = ValidatedInstallDirectory();
        RemoveShortcuts();
        if (TestRoot == null) Registry.CurrentUser.DeleteSubKey(UninstallKey, false);
        ScheduleRemoval(target);
    }

    [STAThread]
    private static int Main(string[] args)
    {
        ConfigureTestRoot(args);
        bool silent = Array.Exists(args, value => value.Equals("--silent", StringComparison.OrdinalIgnoreCase));
        if (!silent && MessageBox.Show("Remove TongaLang and its shortcuts from this computer?", "Uninstall TongaLang", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
            return 0;
        try { Uninstall(); }
        catch (Exception error)
        {
            if (!silent) MessageBox.Show("TongaLang could not be removed.\n\n" + error.Message, "Uninstall TongaLang", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        if (!silent) MessageBox.Show("TongaLang was removed successfully.", "Uninstall TongaLang", MessageBoxButtons.OK, MessageBoxIcon.Information);
        return 0;
    }
}
