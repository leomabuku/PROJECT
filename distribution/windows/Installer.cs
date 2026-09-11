using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("TongaLang Setup")]
[assembly: AssemblyDescription("Per-user installer for the TongaLang educational IDE")]
[assembly: AssemblyCompany("Leo Mabuku")]
[assembly: AssemblyProduct("TongaLang")]
[assembly: AssemblyVersion("0.2.0.0")]
[assembly: AssemblyFileVersion("0.2.0.0")]

internal static class TongaLangInstaller
{
    private const string AppName = "TongaLang";
    private const string Version = "0.2.0";
    private const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\TongaLang";
    private static string TestRoot;

    private static string InstallDirectory
    {
        get
        {
            string root = TestRoot ?? Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            return Path.Combine(root, "Programs", AppName);
        }
    }

    private static string StartMenuDirectory
    {
        get
        {
            if (TestRoot != null) return Path.Combine(TestRoot, "StartMenu", AppName);
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), AppName);
        }
    }

    private static Image LoadLogo()
    {
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("TongaLangLogo"))
        {
            if (stream == null) return null;
            using (Image source = Image.FromStream(stream))
                return new Bitmap(source);
        }
    }

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

    private static void ExtractPayload(string target)
    {
        string root = Path.GetFullPath(target).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("TongaLangPayload"))
        {
            if (stream == null) throw new InvalidOperationException("The installer payload is missing.");
            using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read))
            {
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    string destination = Path.GetFullPath(Path.Combine(target, entry.FullName));
                    if (!destination.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("The installer payload contains an unsafe path.");
                    if (String.IsNullOrEmpty(entry.Name))
                    {
                        Directory.CreateDirectory(destination);
                        continue;
                    }
                    Directory.CreateDirectory(Path.GetDirectoryName(destination));
                    entry.ExtractToFile(destination, true);
                }
            }
        }
    }

    private static void CreateShortcut(string shortcutPath, string targetPath, string description)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(shortcutPath));
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        if (shellType == null) throw new InvalidOperationException("Windows shortcut support is unavailable.");
        dynamic shell = Activator.CreateInstance(shellType);
        dynamic shortcut = shell.CreateShortcut(shortcutPath);
        shortcut.TargetPath = targetPath;
        shortcut.WorkingDirectory = Path.GetDirectoryName(targetPath);
        shortcut.IconLocation = targetPath + ",0";
        shortcut.Description = description;
        shortcut.Save();
    }

    private static void RegisterUninstaller(string target)
    {
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(UninstallKey))
        {
            key.SetValue("DisplayName", AppName);
            key.SetValue("DisplayVersion", Version);
            key.SetValue("Publisher", "Leo Mabuku");
            key.SetValue("InstallLocation", target);
            key.SetValue("DisplayIcon", Path.Combine(target, "TongaLang.exe") + ",0");
            key.SetValue("UninstallString", "\"" + Path.Combine(target, "TongaLang-Uninstall.exe") + "\"");
            key.SetValue("QuietUninstallString", "\"" + Path.Combine(target, "TongaLang-Uninstall.exe") + "\" --silent");
            key.SetValue("URLInfoAbout", "https://github.com/leomabuku/PROJECT");
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
        }
    }

    public static string Install(bool desktopShortcut)
    {
        string target = InstallDirectory;
        string parent = Path.GetDirectoryName(target);
        Directory.CreateDirectory(parent);
        string staging = Path.Combine(parent, "TongaLang-installing-" + Guid.NewGuid().ToString("N"));
        string backup = Path.Combine(parent, "TongaLang.previous");
        Directory.CreateDirectory(staging);
        try
        {
            ExtractPayload(staging);
            if (Directory.Exists(backup)) Directory.Delete(backup, true);
            if (Directory.Exists(target)) Directory.Move(target, backup);
            Directory.Move(staging, target);
            if (Directory.Exists(backup)) Directory.Delete(backup, true);

            string executable = Path.Combine(target, "TongaLang.exe");
            CreateShortcut(Path.Combine(StartMenuDirectory, "TongaLang.lnk"), executable, "Open the TongaLang educational IDE");
            CreateShortcut(Path.Combine(StartMenuDirectory, "Uninstall TongaLang.lnk"), Path.Combine(target, "TongaLang-Uninstall.exe"), "Uninstall TongaLang");
            if (desktopShortcut)
                CreateShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "TongaLang.lnk"), executable, "Open the TongaLang educational IDE");
            if (TestRoot == null) RegisterUninstaller(target);
            return executable;
        }
        catch
        {
            if (Directory.Exists(staging)) Directory.Delete(staging, true);
            if (!Directory.Exists(target) && Directory.Exists(backup)) Directory.Move(backup, target);
            throw;
        }
    }

    [STAThread]
    private static int Main(string[] args)
    {
        ConfigureTestRoot(args);
        bool silent = Array.Exists(args, value => value.Equals("--silent", StringComparison.OrdinalIgnoreCase));
        bool noDesktop = Array.Exists(args, value => value.Equals("--no-desktop", StringComparison.OrdinalIgnoreCase));
        bool launch = Array.Exists(args, value => value.Equals("--launch", StringComparison.OrdinalIgnoreCase));
        if (silent)
        {
            try
            {
                string executable = Install(!noDesktop);
                if (launch) Process.Start(executable);
                return 0;
            }
            catch (Exception error)
            {
                try
                {
                    string logDirectory = TestRoot ?? Path.GetTempPath();
                    Directory.CreateDirectory(logDirectory);
                    File.WriteAllText(Path.Combine(logDirectory, "TongaLang-install-error.txt"), error.ToString());
                }
                catch { }
                return 1;
            }
        }
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new InstallerForm());
        return 0;
    }

    private sealed class InstallerForm : Form
    {
        private readonly CheckBox desktop = new CheckBox();
        private readonly Label status = new Label();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly Button install = new Button();

        public InstallerForm()
        {
            Text = "TongaLang Setup";
            ClientSize = new Size(640, 410);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            BackColor = Color.FromArgb(11, 16, 32);
            ForeColor = Color.FromArgb(229, 231, 235);
            Font = new Font("Segoe UI", 10F);
            Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);

            Image logo = LoadLogo();
            if (logo != null)
            {
                PictureBox picture = new PictureBox();
                picture.Image = logo;
                picture.SizeMode = PictureBoxSizeMode.Zoom;
                picture.BackColor = BackColor;
                picture.SetBounds(28, 20, 68, 68);
                Controls.Add(picture);
            }
            Controls.Add(MakeLabel("TongaLang", 110, 24, 490, 42, 24F, true));
            Controls.Add(MakeLabel("Beginner programming language · Version " + Version, 112, 67, 488, 28, 10F, false));
            Controls.Add(MakeLabel("Install TongaLang for this Windows user", 30, 122, 560, 30, 15F, true));
            Controls.Add(MakeLabel("Setup includes the educational IDE, language guide, examples, Start Menu shortcut and uninstaller. Administrator access is not required.", 30, 162, 570, 46, 10F, false));
            Controls.Add(MakeLabel("Install location", 30, 216, 560, 22, 9F, true));
            Label path = MakeLabel(@"%LOCALAPPDATA%\Programs\TongaLang", 30, 242, 570, 34, 9F, false);
            path.BackColor = Color.FromArgb(23, 32, 51);
            path.Padding = new Padding(7);
            Controls.Add(path);
            desktop.Text = "Create a Desktop shortcut";
            desktop.Checked = true;
            desktop.SetBounds(30, 288, 300, 26);
            desktop.BackColor = BackColor;
            desktop.ForeColor = ForeColor;
            Controls.Add(desktop);
            status.Text = "Ready to install.";
            status.SetBounds(30, 322, 570, 22);
            status.ForeColor = Color.FromArgb(148, 163, 184);
            Controls.Add(status);
            progress.SetBounds(30, 347, 570, 12);
            Controls.Add(progress);
            install.Text = "Install TongaLang";
            install.SetBounds(422, 370, 128, 30);
            install.BackColor = Color.FromArgb(34, 197, 94);
            install.Click += InstallClicked;
            Controls.Add(install);
            Button cancel = new Button { Text = "Cancel" };
            cancel.SetBounds(555, 370, 70, 30);
            cancel.Click += delegate { Close(); };
            Controls.Add(cancel);
        }

        private Label MakeLabel(string text, int x, int y, int width, int height, float size, bool bold)
        {
            Label label = new Label();
            label.Text = text;
            label.SetBounds(x, y, width, height);
            label.ForeColor = bold ? ForeColor : Color.FromArgb(203, 213, 225);
            label.BackColor = BackColor;
            label.Font = new Font("Segoe UI", size, bold ? FontStyle.Bold : FontStyle.Regular);
            return label;
        }

        private void InstallClicked(object sender, EventArgs eventArgs)
        {
            install.Enabled = false;
            progress.Style = ProgressBarStyle.Marquee;
            status.Text = "Installing TongaLang…";
            Refresh();
            try
            {
                string executable = Install(desktop.Checked);
                progress.Style = ProgressBarStyle.Blocks;
                progress.Value = 100;
                status.Text = "TongaLang was installed successfully.";
                if (MessageBox.Show("Installation is complete. Open TongaLang now?", "TongaLang Setup", MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
                    Process.Start(executable);
                Close();
            }
            catch (Exception error)
            {
                progress.Style = ProgressBarStyle.Blocks;
                status.Text = "Installation did not complete.";
                install.Enabled = true;
                MessageBox.Show("TongaLang could not be installed.\n\n" + error.Message, "TongaLang Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
