using System.Diagnostics;
using System.IO.Compression;
using System.Reflection;
using System.Text;
using Microsoft.Win32;

namespace HXSSKoreanPatchInstaller;

internal static class Program
{
    private const string AppId = "2389170";
    private const string GameExe = "hxss.exe";
    private const string PatchTitle = "화하: 전국시대 한글 패치";
    private const string StateDir = "HXSS_Korean_Localization\\InstallerState";
    private const string ManifestName = "installed_manifest.tsv";
    private const string PayloadResourceName = "payload.zip";

    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new InstallerForm());
    }

    private sealed class InstallerForm : Form
    {
        private readonly TextBox targetBox = new();
        private readonly TextBox logBox = new();
        private readonly Button installButton = new();
        private readonly Button uninstallButton = new();
        private readonly Label statusLabel = new();

        public InstallerForm()
        {
            Text = PatchTitle;
            Width = 760;
            Height = 520;
            MinimumSize = new Size(680, 440);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);

            var root = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 1,
                RowCount = 5,
                Padding = new Padding(18),
            };
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            Controls.Add(root);

            var title = new Label
            {
                Text = PatchTitle,
                AutoSize = true,
                Font = new Font(Font, FontStyle.Bold),
                Margin = new Padding(0, 0, 0, 8),
            };
            root.Controls.Add(title);

            statusLabel.AutoSize = true;
            statusLabel.Margin = new Padding(0, 0, 0, 14);
            root.Controls.Add(statusLabel);

            var pathRow = new TableLayoutPanel
            {
                Dock = DockStyle.Top,
                ColumnCount = 3,
                AutoSize = true,
                Margin = new Padding(0, 0, 0, 12),
            };
            pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            root.Controls.Add(pathRow);

            pathRow.Controls.Add(new Label
            {
                Text = "설치 위치",
                AutoSize = true,
                Anchor = AnchorStyles.Left,
                Margin = new Padding(0, 4, 10, 0),
            }, 0, 0);

            targetBox.Dock = DockStyle.Fill;
            pathRow.Controls.Add(targetBox, 1, 0);

            var browseButton = new Button
            {
                Text = "찾아보기",
                AutoSize = true,
                Margin = new Padding(8, 0, 0, 0),
            };
            browseButton.Click += (_, _) => BrowseTarget();
            pathRow.Controls.Add(browseButton, 2, 0);

            var buttonRow = new FlowLayoutPanel
            {
                Dock = DockStyle.Top,
                AutoSize = true,
                FlowDirection = FlowDirection.LeftToRight,
                Margin = new Padding(0, 0, 0, 12),
            };
            root.Controls.Add(buttonRow);

            installButton.Text = "설치";
            installButton.Width = 120;
            installButton.Click += (_, _) => RunOperation(InstallPatch);
            buttonRow.Controls.Add(installButton);

            uninstallButton.Text = "제거";
            uninstallButton.Width = 120;
            uninstallButton.Margin = new Padding(8, 0, 0, 0);
            uninstallButton.Click += (_, _) => RunOperation(UninstallPatch);
            buttonRow.Controls.Add(uninstallButton);

            logBox.Dock = DockStyle.Fill;
            logBox.Multiline = true;
            logBox.ScrollBars = ScrollBars.Vertical;
            logBox.ReadOnly = true;
            root.Controls.Add(logBox);

            var closeButton = new Button
            {
                Text = "닫기",
                Width = 120,
                Anchor = AnchorStyles.Right,
                Margin = new Padding(0, 12, 0, 0),
            };
            closeButton.Click += (_, _) => Close();
            root.Controls.Add(closeButton);

            var detected = SteamLocator.FindGamePath();
            targetBox.Text = detected ?? "";
            statusLabel.Text = detected is null
                ? "Steam 설치 정보를 찾지 못했습니다. 설치 위치를 직접 선택하세요."
                : "Steam 설치 정보를 확인했습니다. 기본 설치 위치를 자동 입력했습니다.";
        }

        private void BrowseTarget()
        {
            using var dialog = new FolderBrowserDialog
            {
                Description = "화하: 전국시대 설치 폴더를 선택하세요.",
                UseDescriptionForTitle = true,
                SelectedPath = Directory.Exists(targetBox.Text) ? targetBox.Text : Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
            };

            if (dialog.ShowDialog(this) == DialogResult.OK)
            {
                targetBox.Text = dialog.SelectedPath;
            }
        }

        private void RunOperation(Action<string> operation)
        {
            var target = targetBox.Text.Trim().Trim('"');
            if (!ValidateTarget(target))
            {
                MessageBox.Show(this, "선택한 폴더에서 hxss.exe를 찾지 못했습니다. 게임 설치 폴더를 선택하세요.", PatchTitle, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            installButton.Enabled = false;
            uninstallButton.Enabled = false;
            try
            {
                operation(target);
            }
            catch (Exception ex)
            {
                Log("오류: " + ex.Message);
                MessageBox.Show(this, ex.Message, PatchTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                installButton.Enabled = true;
                uninstallButton.Enabled = true;
            }
        }

        private static bool ValidateTarget(string target)
        {
            return Directory.Exists(target) && File.Exists(Path.Combine(target, GameExe));
        }

        private void InstallPatch(string target)
        {
            Log("설치를 시작합니다.");
            var existingManifest = Path.Combine(target, StateDir, ManifestName);
            if (File.Exists(existingManifest))
            {
                Log("기존 설치 기록을 찾았습니다. 이전 패치를 먼저 제거합니다.");
                RemoveInstalledPatch(target, showMissingManifestWarning: false, showCompletionMessage: false);
            }

            using var temp = TempDirectory.Create();
            var payloadZip = Path.Combine(temp.Path, "payload.zip");
            ExtractPayloadResource(payloadZip);
            ZipFile.ExtractToDirectory(payloadZip, temp.Path);

            var files = Directory.EnumerateFiles(temp.Path, "*", SearchOption.AllDirectories)
                .Where(path => !Path.GetFileName(path).Equals("payload.zip", StringComparison.OrdinalIgnoreCase))
                .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
                .ToList();

            var stateRoot = Path.Combine(target, StateDir);
            var backupRoot = Path.Combine(stateRoot, "Backup", DateTime.Now.ToString("yyyyMMdd_HHmmss"));
            Directory.CreateDirectory(stateRoot);
            Directory.CreateDirectory(backupRoot);

            var records = new List<InstallRecord>();
            foreach (var source in files)
            {
                var relative = Path.GetRelativePath(temp.Path, source);
                var destination = Path.Combine(target, relative);
                var backupRelative = "";

                if (File.Exists(destination))
                {
                    backupRelative = Path.Combine("Backup", Path.GetFileName(backupRoot), relative);
                    var backupPath = Path.Combine(stateRoot, backupRelative);
                    Directory.CreateDirectory(Path.GetDirectoryName(backupPath)!);
                    File.Copy(destination, backupPath, overwrite: true);
                }

                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Copy(source, destination, overwrite: true);
                records.Add(new InstallRecord(relative, backupRelative));
                Log("설치: " + relative);
            }

            WriteManifest(Path.Combine(stateRoot, ManifestName), records);
            Log("설치가 완료되었습니다.");
            MessageBox.Show(this, "한글 패치 설치가 완료되었습니다.", PatchTitle, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void UninstallPatch(string target)
        {
            RemoveInstalledPatch(target, showMissingManifestWarning: true, showCompletionMessage: true);
        }

        private void RemoveInstalledPatch(string target, bool showMissingManifestWarning, bool showCompletionMessage)
        {
            var stateRoot = Path.Combine(target, StateDir);
            var manifestPath = Path.Combine(stateRoot, ManifestName);
            if (!File.Exists(manifestPath))
            {
                if (showMissingManifestWarning)
                {
                    MessageBox.Show(this, "설치 기록을 찾지 못했습니다. 이 설치기로 설치한 패치만 자동 제거할 수 있습니다.", PatchTitle, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
                return;
            }

            Log("제거를 시작합니다.");
            var records = ReadManifest(manifestPath);
            foreach (var record in records.AsEnumerable().Reverse())
            {
                var destination = Path.Combine(target, record.RelativePath);
                if (!string.IsNullOrWhiteSpace(record.BackupRelativePath))
                {
                    var backupPath = Path.Combine(stateRoot, record.BackupRelativePath);
                    if (File.Exists(backupPath))
                    {
                        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                        File.Copy(backupPath, destination, overwrite: true);
                        Log("복원: " + record.RelativePath);
                        continue;
                    }
                }

                if (File.Exists(destination))
                {
                    File.Delete(destination);
                    Log("삭제: " + record.RelativePath);
                }
            }

            RemoveEmptyPatchDirectories(target);
            File.Delete(manifestPath);
            Log("제거가 완료되었습니다.");
            if (showCompletionMessage)
            {
                MessageBox.Show(this, "한글 패치 제거가 완료되었습니다.", PatchTitle, MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }

        private static void RemoveEmptyPatchDirectories(string target)
        {
            foreach (var relative in new[]
            {
                "BepInEx\\plugins\\HXSS.HuiWenFontReplacer\\KoreanPatch\\lua\\game\\config",
                "BepInEx\\plugins\\HXSS.HuiWenFontReplacer\\KoreanPatch\\lua\\game",
                "BepInEx\\plugins\\HXSS.HuiWenFontReplacer\\KoreanPatch\\lua",
                "BepInEx\\plugins\\HXSS.HuiWenFontReplacer\\KoreanPatch",
                "BepInEx\\plugins\\HXSS.HuiWenFontReplacer",
                "HXSS_Korean_Localization\\MaintenanceKit\\output",
                "HXSS_Korean_Localization\\MaintenanceKit",
                "HXSS_Korean_Localization\\00_Project_Docs",
                "HXSS_Korean_Localization\\03_Font_Work\\Font\\HuiWenFontReplacer",
            }.OrderByDescending(x => x.Length))
            {
                var path = Path.Combine(target, relative);
                if (Directory.Exists(path) && !Directory.EnumerateFileSystemEntries(path).Any())
                {
                    Directory.Delete(path);
                }
            }
        }

        private static void ExtractPayloadResource(string outputPath)
        {
            using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(PayloadResourceName)
                ?? throw new InvalidOperationException("설치 페이로드를 찾지 못했습니다.");
            using var file = File.Create(outputPath);
            stream.CopyTo(file);
        }

        private static void WriteManifest(string path, IEnumerable<InstallRecord> records)
        {
            using var writer = new StreamWriter(path, false, new UTF8Encoding(false));
            writer.WriteLine("relative_path\tbackup_relative_path");
            foreach (var record in records)
            {
                writer.WriteLine($"{Escape(record.RelativePath)}\t{Escape(record.BackupRelativePath)}");
            }
        }

        private static List<InstallRecord> ReadManifest(string path)
        {
            var result = new List<InstallRecord>();
            foreach (var line in File.ReadLines(path, Encoding.UTF8).Skip(1))
            {
                if (string.IsNullOrWhiteSpace(line))
                {
                    continue;
                }

                var parts = line.Split('\t');
                result.Add(new InstallRecord(Unescape(parts.ElementAtOrDefault(0) ?? ""), Unescape(parts.ElementAtOrDefault(1) ?? "")));
            }

            return result;
        }

        private static string Escape(string value) => value.Replace("\\", "/");
        private static string Unescape(string value) => value.Replace("/", "\\");

        private void Log(string message)
        {
            logBox.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}{Environment.NewLine}");
        }
    }

    private sealed record InstallRecord(string RelativePath, string BackupRelativePath);

    private sealed class TempDirectory : IDisposable
    {
        public string Path { get; }

        private TempDirectory(string path)
        {
            Path = path;
        }

        public static TempDirectory Create()
        {
            var path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "HXSS_KoreanPatch_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(path);
            return new TempDirectory(path);
        }

        public void Dispose()
        {
            try
            {
                if (Directory.Exists(Path))
                {
                    Directory.Delete(Path, recursive: true);
                }
            }
            catch
            {
                // Temporary cleanup failure should not affect install result.
            }
        }
    }

    private static class SteamLocator
    {
        public static string? FindGamePath()
        {
            foreach (var steamPath in FindSteamRoots())
            {
                foreach (var library in FindLibraryFolders(steamPath))
                {
                    var manifest = Path.Combine(library, "steamapps", $"appmanifest_{AppId}.acf");
                    if (!File.Exists(manifest))
                    {
                        continue;
                    }

                    var installDir = ReadAcfValue(manifest, "installdir");
                    if (string.IsNullOrWhiteSpace(installDir))
                    {
                        installDir = "HuaXia Warring States";
                    }

                    var candidate = Path.Combine(library, "steamapps", "common", installDir);
                    if (File.Exists(Path.Combine(candidate, GameExe)))
                    {
                        return candidate;
                    }
                }
            }

            return null;
        }

        private static IEnumerable<string> FindSteamRoots()
        {
            var keys = new[]
            {
                @"HKEY_CURRENT_USER\Software\Valve\Steam",
                @"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam",
                @"HKEY_LOCAL_MACHINE\SOFTWARE\Valve\Steam",
            };

            foreach (var key in keys)
            {
                foreach (var valueName in new[] { "SteamPath", "InstallPath" })
                {
                    var value = Registry.GetValue(key, valueName, null)?.ToString();
                    if (!string.IsNullOrWhiteSpace(value) && Directory.Exists(value))
                    {
                        yield return value.Replace('/', '\\');
                    }
                }
            }
        }

        private static IEnumerable<string> FindLibraryFolders(string steamRoot)
        {
            yield return steamRoot;

            var libraryFile = Path.Combine(steamRoot, "steamapps", "libraryfolders.vdf");
            if (!File.Exists(libraryFile))
            {
                yield break;
            }

            foreach (var line in File.ReadLines(libraryFile))
            {
                var path = TryReadVdfPath(line);
                if (!string.IsNullOrWhiteSpace(path) && Directory.Exists(path))
                {
                    yield return path;
                }
            }
        }

        private static string? TryReadVdfPath(string line)
        {
            var trimmed = line.Trim();
            if (!trimmed.StartsWith("\"path\"", StringComparison.OrdinalIgnoreCase))
            {
                return null;
            }

            var parts = trimmed.Split('"', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 2)
            {
                return null;
            }

            return parts[1].Replace(@"\\", @"\");
        }

        private static string? ReadAcfValue(string manifest, string key)
        {
            foreach (var line in File.ReadLines(manifest))
            {
                var trimmed = line.Trim();
                if (!trimmed.StartsWith($"\"{key}\"", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                var parts = trimmed.Split('"', StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length >= 2)
                {
                    return parts[1];
                }
            }

            return null;
        }
    }
}
