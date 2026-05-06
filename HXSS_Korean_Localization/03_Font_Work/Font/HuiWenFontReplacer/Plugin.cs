using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using Il2CppInterop.Runtime.Injection;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using TMPro;
using UnityEngine;

namespace HXSS.HuiWenFontReplacer;

[BepInPlugin("hxss.huiwen-font-replacer", "HXSS HuiWen Font Replacer", "0.1.0")]
public sealed class Plugin : BasePlugin
{
    internal static ManualLogSource PluginLog = null!;
    internal static ConfigEntry<bool> EnableFontReplacement = null!;
    internal static ConfigEntry<bool> EnableFontFallback = null!;
    internal static ConfigEntry<bool> EnableFontOverride = null!;
    internal static ConfigEntry<bool> EnableTextOverrides = null!;
    internal static ConfigEntry<bool> EnableTextOverrideScan = null!;
    internal static ConfigEntry<bool> EnableChineseCollector = null!;
    internal static ConfigEntry<bool> EnableLuaLoadTrace = null!;
    internal static ConfigEntry<bool> EnableFontDebug = null!;
    internal static ConfigEntry<float> UiScanIntervalSeconds = null!;

    public override void Load()
    {
        PluginLog = Log;
        EnableFontReplacement = Config.Bind(
            "General",
            "EnableFontReplacement",
            true,
            "Master switch for Korean font support.");
        EnableFontFallback = Config.Bind(
            "General",
            "EnableFontFallback",
            true,
            "Add the bundled Korean/Chinese merged font to TextMeshPro fallback fonts. Recommended for normal play.");
        EnableFontOverride = Config.Bind(
            "General",
            "EnableFontOverride",
            false,
            "Force specific UI fonts to be replaced during periodic UI scans. Disabled by default because fallback handles square-box prevention with lower risk.");
        EnableTextOverrides = Config.Bind(
            "General",
            "EnableTextOverrides",
            true,
            "Apply hardcoded_text.tsv replacements for UI strings that are not covered by the Lua language tables.");
        EnableTextOverrideScan = Config.Bind(
            "General",
            "EnableTextOverrideScan",
            true,
            "Apply hardcoded_text.tsv replacements during periodic UI scans.");
        EnableChineseCollector = Config.Bind(
            "Collector",
            "EnableChineseCollector",
            false,
            "Collect untranslated Chinese UI strings to collected_chinese.tsv after Korean title-start text is detected. Keep disabled for normal play/release.");
        EnableLuaLoadTrace = Config.Bind(
            "Debug",
            "EnableLuaLoadTrace",
            false,
            "Write lua_loader_trace.tsv entries when language Lua files are redirected. Useful only for maintenance debugging.");
        EnableFontDebug = Config.Bind(
            "Debug",
            "EnableFontDebug",
            false,
            "Write font_debug.tsv rows for Korean or square-box UI text with its TMP/UI font name and object path. Useful only for maintenance debugging.");
        UiScanIntervalSeconds = Config.Bind(
            "Performance",
            "UiScanIntervalSeconds",
            2.0f,
            "Seconds between lightweight UI scans for font replacement and hardcoded UI overrides.");
        Harmony.CreateAndPatchAll(typeof(CXLuaMgr_CustomLuaFilePath_Patch));
        ClassInjector.RegisterTypeInIl2Cpp<FontReplaceBehaviour>();
        AddComponent<FontReplaceBehaviour>();
        Log.LogInfo("HXSS HuiWen Font Replacer loaded.");
    }
}

[HarmonyPatch(typeof(CXLuaMgr), nameof(CXLuaMgr.CustomLuaFilePath))]
internal static class CXLuaMgr_CustomLuaFilePath_Patch
{
    private const int MaxTraceLines = 3000;
    private static readonly HashSet<string> SeenFileNames = new(StringComparer.OrdinalIgnoreCase);
    private static int _traceLineCount;

    private static void Prefix(ref string fileName, out string __state)
    {
        __state = fileName;
        if (TryGetKoreanLuaPath(fileName, out string? patchPath))
        {
            fileName = patchPath!;
        }
    }

    private static void Postfix(string __state, ref string fileName, Il2CppStructArray<byte>? __result)
    {
        string originalFileName = string.IsNullOrWhiteSpace(__state) ? fileName : __state;
        if (string.IsNullOrWhiteSpace(originalFileName))
        {
            return;
        }

        bool replaced = !string.Equals(originalFileName, fileName, StringComparison.OrdinalIgnoreCase);
        bool shouldTrace = replaced
            || originalFileName.IndexOf("language", StringComparison.OrdinalIgnoreCase) >= 0
            || originalFileName.IndexOf("config", StringComparison.OrdinalIgnoreCase) >= 0
            || originalFileName.IndexOf("task", StringComparison.OrdinalIgnoreCase) >= 0;

        if (shouldTrace)
        {
            int resultLength = __result == null ? -1 : __result.Length;
            TraceLuaLoad(originalFileName, fileName, resultLength, replaced);
        }
    }

    private static bool TryGetKoreanLuaPath(string fileName, out string? patchPath)
    {
        patchPath = null;
        string normalized = fileName.Replace('\\', '/');
        string? patchFileName = null;
        if (IsLuaModule(normalized, "t_language"))
        {
            patchFileName = "t_language.lua";
        }
        else if (IsLuaModule(normalized, "t_taskLanguage"))
        {
            patchFileName = "t_taskLanguage.lua";
        }

        if (patchFileName == null)
        {
            return false;
        }

        string absolutePatchPath = Path.Combine(
            Paths.PluginPath,
            "HXSS.HuiWenFontReplacer",
            "KoreanPatch",
            "lua",
            "game",
            "config",
            patchFileName);

        if (!File.Exists(absolutePatchPath))
        {
            Plugin.PluginLog.LogWarning($"Korean Lua patch file not found: {absolutePatchPath}");
            patchPath = null;
            return false;
        }

        // CXLuaMgr.CustomLuaFilePath receives module names such as
        // "game/config/t_language" and internally builds:
        //   <GameRoot>/hxss_Data/StreamingAssets/lua/<fileName>.lua
        // Passing an absolute path causes invalid paths like
        //   .../StreamingAssets/lua/C:\...\t_language.lua.lua
        // so provide a traversal path relative to StreamingAssets/lua instead.
        patchPath = Path.Combine(
                "..",
                "..",
                "..",
                "BepInEx",
                "plugins",
                "HXSS.HuiWenFontReplacer",
                "KoreanPatch",
                "lua",
                "game",
                "config",
                Path.GetFileNameWithoutExtension(patchFileName))
            .Replace('\\', '/');

        return true;
    }

    private static bool IsLuaModule(string normalizedPathOrModule, string moduleName)
    {
        return normalizedPathOrModule.EndsWith("/" + moduleName + ".lua", StringComparison.OrdinalIgnoreCase)
            || normalizedPathOrModule.EndsWith("/" + moduleName, StringComparison.OrdinalIgnoreCase)
            || string.Equals(normalizedPathOrModule, moduleName, StringComparison.OrdinalIgnoreCase)
            || string.Equals(normalizedPathOrModule, "game/config/" + moduleName, StringComparison.OrdinalIgnoreCase);
    }

    private static void TraceLuaLoad(string originalFileName, string actualFileName, int resultLength, bool replaced)
    {
        if (!Plugin.EnableLuaLoadTrace.Value)
        {
            return;
        }

        string traceKey = (replaced ? "patched:" : "source:") + originalFileName;
        if (_traceLineCount >= MaxTraceLines || !SeenFileNames.Add(traceKey))
        {
            return;
        }

        try
        {
            string pluginDir = Path.Combine(Paths.PluginPath, "HXSS.HuiWenFontReplacer");
            Directory.CreateDirectory(pluginDir);
            string tracePath = Path.Combine(pluginDir, "lua_loader_trace.tsv");
            if (!File.Exists(tracePath))
            {
                File.WriteAllText(tracePath, "original_file\tactual_file\tresult_bytes\treplaced\tseen_unix\n", new UTF8Encoding(false));
            }

            string line = EscapeForTsv(originalFileName)
                + "\t" + EscapeForTsv(actualFileName)
                + "\t" + resultLength.ToString(System.Globalization.CultureInfo.InvariantCulture)
                + "\t" + (replaced ? "1" : "0")
                + "\t" + DateTimeOffset.UtcNow.ToUnixTimeSeconds()
                + Environment.NewLine;
            File.AppendAllText(tracePath, line, new UTF8Encoding(false));
            _traceLineCount++;
        }
        catch (Exception ex)
        {
            Plugin.PluginLog.LogWarning($"Failed to trace Lua loader path: {ex.Message}");
        }
    }

    private static string EscapeForTsv(string value)
    {
        return value
            .Replace("\r", "\\r", StringComparison.Ordinal)
            .Replace("\n", "\\n", StringComparison.Ordinal)
            .Replace("\t", "\\t", StringComparison.Ordinal);
    }
}

public sealed class FontReplaceBehaviour : MonoBehaviour
{
    private const string TargetFontName = "HuiWenZhengKai";
    private const string SourceHanFontName = "SourceHanSerifCN-Bold";
    private const string AlibabaReplacementTmpFontName = "AlibabaPuHuiTi-Regular SDF";
    private const string ReplacementFontFileName = "Shilla_HuiWen_CN_KR_Strict.ttf";
    private const string OverrideFileName = "hardcoded_text.tsv";
    private const string CollectorFileName = "collected_chinese.tsv";
    private const string FontDebugFileName = "font_debug.tsv";

    private Font? _replacementFont;
    private TMP_FontAsset? _replacementTmpFont;
    private TMP_FontAsset? _alibabaReplacementTmpFont;
    private readonly Dictionary<string, string> _textOverrides = new(StringComparer.Ordinal);
    private readonly HashSet<string> _collectedChinese = new(StringComparer.Ordinal);
    private readonly HashSet<string> _fontDebugEntries = new(StringComparer.Ordinal);
    private string? _overridePath;
    private DateTime _overrideLastWriteUtc;
    private string? _collectorPath;
    private bool _koreanCollectionUnlocked;
    private bool _koreanUiActiveForCollection;
    private float _nextScanAt;
    private int _lastUiTextReplaced = -1;
    private int _lastTmpTextReplaced = -1;
    private int _lastUiTextCandidates = -1;
    private int _lastTmpTextCandidates = -1;
    private int _lastUiOverridesApplied = -1;
    private int _lastTmpOverridesApplied = -1;
    private string? _fontDebugPath;
    private bool _loggedMissingAlibabaTmpFont;
    private int _lastTmpFallbackFontsMapped = -1;

    public FontReplaceBehaviour(IntPtr ptr) : base(ptr)
    {
    }

    private void Start()
    {
        DontDestroyOnLoad(gameObject);
        if (Plugin.EnableFontReplacement.Value
            && (Plugin.EnableFontFallback.Value || Plugin.EnableFontOverride.Value))
        {
            LoadReplacementFont();
        }

        if (Plugin.EnableFontDebug.Value)
        {
            _fontDebugPath = Path.Combine(Paths.PluginPath, "HXSS.HuiWenFontReplacer", FontDebugFileName);
            File.WriteAllText(_fontDebugPath, "kind\tfont\tobjectPath\ttext\n", Encoding.UTF8);
        }

        if (Plugin.EnableTextOverrides.Value)
        {
            LoadTextOverrides();
        }

        if (Plugin.EnableChineseCollector.Value)
        {
            LoadCollectorCache();
        }
    }

    private void Update()
    {
        bool shouldScanFonts = Plugin.EnableFontReplacement.Value && Plugin.EnableFontOverride.Value;
        bool shouldApplyFontFallbacks = Plugin.EnableFontReplacement.Value && Plugin.EnableFontFallback.Value;
        bool shouldScanTextOverrides = Plugin.EnableTextOverrides.Value && Plugin.EnableTextOverrideScan.Value;
        bool shouldScanTexts = shouldScanFonts
            || shouldScanTextOverrides
            || Plugin.EnableFontDebug.Value
            || Plugin.EnableChineseCollector.Value;
        if (!shouldScanFonts
            && !shouldApplyFontFallbacks
            && !Plugin.EnableFontDebug.Value
            && !shouldScanTextOverrides
            && !Plugin.EnableChineseCollector.Value)
        {
            return;
        }

        if (Time.unscaledTime < _nextScanAt)
        {
            return;
        }

        _nextScanAt = Time.unscaledTime + Math.Max(0.5f, Plugin.UiScanIntervalSeconds.Value);

        if (Plugin.EnableTextOverrides.Value)
        {
            ReloadTextOverridesIfChanged();
        }

        if (shouldApplyFontFallbacks)
        {
            ApplyTargetedTmpFontFallbacks();
        }

        if (Plugin.EnableChineseCollector.Value && !_koreanCollectionUnlocked && HasKoreanTitleStartText())
        {
            _koreanCollectionUnlocked = true;
            Plugin.PluginLog.LogInfo("Chinese text collection unlocked by Korean title start text.");
        }

        if (!shouldScanTexts)
        {
            return;
        }

        _koreanUiActiveForCollection = Plugin.EnableChineseCollector.Value && _koreanCollectionUnlocked;
        ProcessUnityUiTexts();
        ProcessTmpTexts();
    }

    private void LoadReplacementFont()
    {
        string fontPath = FindReplacementFontPath();
        if (!File.Exists(fontPath))
        {
            Plugin.PluginLog.LogWarning($"Replacement font not found: {fontPath}");
            return;
        }

        try
        {
            _replacementFont = new Font(fontPath);
            _replacementFont.name = "Shilla_HuiWen_CN_KR_Strict_HXSS";
            _replacementTmpFont = TMP_FontAsset.CreateFontAsset(_replacementFont);
            _replacementTmpFont.name = "Shilla_HuiWen_CN_KR_Strict_HXSS SDF";
            _replacementTmpFont.atlasPopulationMode = AtlasPopulationMode.Dynamic;
            if (Plugin.EnableFontFallback.Value)
            {
                ApplyTargetedTmpFontFallbacks();
            }
            Plugin.PluginLog.LogInfo($"Replacement font loaded: {fontPath}");
        }
        catch (Exception ex)
        {
            Plugin.PluginLog.LogError($"Failed to load replacement font from {fontPath}: {ex}");
            _replacementFont = null;
            _replacementTmpFont = null;
        }
    }

    private void ApplyTargetedTmpFontFallbacks()
    {
        if (_replacementTmpFont == null)
        {
            return;
        }

        try
        {
            TMP_FontAsset? alibabaReplacementTmpFont = ResolveAlibabaReplacementTmpFont();
            var fontAssets = Resources.FindObjectsOfTypeAll<TMP_FontAsset>();
            int mapped = 0;
            foreach (var fontAsset in fontAssets)
            {
                if (fontAsset == null || string.IsNullOrWhiteSpace(fontAsset.name))
                {
                    continue;
                }

                if (IsSourceHanFont(fontAsset.name)
                    && alibabaReplacementTmpFont != null
                    && AddFallbackFont(fontAsset, alibabaReplacementTmpFont))
                {
                    mapped++;
                }
                else if (IsTargetFont(fontAsset.name)
                    && AddFallbackFont(fontAsset, _replacementTmpFont))
                {
                    mapped++;
                }
            }

            if (mapped != _lastTmpFallbackFontsMapped)
            {
                _lastTmpFallbackFontsMapped = mapped;
                Plugin.PluginLog.LogInfo($"TMP targeted fallback fonts mapped={mapped}");
            }
        }
        catch (Exception ex)
        {
            Plugin.PluginLog.LogWarning($"Failed to map TMP targeted fallback fonts: {ex.Message}");
        }
    }

    private static bool AddFallbackFont(TMP_FontAsset fontAsset, TMP_FontAsset fallbackFontAsset)
    {
        if (fontAsset == fallbackFontAsset)
        {
            return false;
        }

        if (fontAsset.fallbackFontAssetTable == null)
        {
            fontAsset.fallbackFontAssetTable = new Il2CppSystem.Collections.Generic.List<TMP_FontAsset>();
        }

        if (fontAsset.fallbackFontAssetTable.Contains(fallbackFontAsset))
        {
            return false;
        }

        fontAsset.fallbackFontAssetTable.Insert(0, fallbackFontAsset);
        return true;
    }

    private static string FindReplacementFontPath()
    {
        string pluginPath = Path.Combine(Paths.PluginPath, "HXSS.HuiWenFontReplacer", ReplacementFontFileName);
        if (File.Exists(pluginPath))
        {
            return pluginPath;
        }

        return Path.Combine(
            Paths.GameRootPath,
            "BepInEx",
            "Translation",
            "ko",
            "Font",
            "추출 폰트",
            "대체용 폰트",
            ReplacementFontFileName);
    }

    private void ProcessUnityUiTexts()
    {
        var texts = Resources.FindObjectsOfTypeAll<UnityEngine.UI.Text>();
        int fontCandidates = 0;
        int fontReplaced = 0;
        int overridesApplied = 0;
        foreach (var text in texts)
        {
            if (text == null)
            {
                continue;
            }

            if (Plugin.EnableFontDebug.Value)
            {
                LogFontDebug("UnityText", text.font == null ? string.Empty : text.font.name, GetGameObjectPath(text.gameObject), text.text);
            }

            if (Plugin.EnableFontReplacement.Value
                && Plugin.EnableFontOverride.Value
                && _replacementFont != null
                && text.font != null
                && IsTargetFont(text.font.name))
            {
                fontCandidates++;
                text.font = _replacementFont;
                text.SetAllDirty();
                fontReplaced++;
            }

            string? value = text.text;
            if (Plugin.EnableTextOverrides.Value
                && Plugin.EnableTextOverrideScan.Value
                && TryGetOverride(value, out string? replacement))
            {
                text.text = replacement;
                text.SetAllDirty();
                overridesApplied++;
                continue;
            }

            CollectChineseText(value);
        }

        if (fontReplaced != _lastUiTextReplaced || fontCandidates != _lastUiTextCandidates)
        {
            _lastUiTextReplaced = fontReplaced;
            _lastUiTextCandidates = fontCandidates;
            Plugin.PluginLog.LogInfo($"Unity UI Text font candidates={fontCandidates}, replaced={fontReplaced}");
        }

        if (overridesApplied != _lastUiOverridesApplied)
        {
            _lastUiOverridesApplied = overridesApplied;
            Plugin.PluginLog.LogInfo($"Unity UI Text overrides applied={overridesApplied}");
        }
    }

    private void ProcessTmpTexts()
    {
        var texts = Resources.FindObjectsOfTypeAll<TMP_Text>();
        TMP_FontAsset? alibabaReplacementTmpFont = Plugin.EnableFontReplacement.Value && Plugin.EnableFontOverride.Value
            ? ResolveAlibabaReplacementTmpFont()
            : null;
        int fontCandidates = 0;
        int fontReplaced = 0;
        int overridesApplied = 0;
        foreach (var text in texts)
        {
            if (text == null)
            {
                continue;
            }

            if (Plugin.EnableFontDebug.Value)
            {
                LogFontDebug("TMP", text.font == null ? string.Empty : text.font.name, GetGameObjectPath(text.gameObject), text.text);
            }

            if (Plugin.EnableFontReplacement.Value && Plugin.EnableFontOverride.Value && text.font != null)
            {
                if (alibabaReplacementTmpFont != null && IsSourceHanFont(text.font.name))
                {
                    fontCandidates++;
                    text.font = alibabaReplacementTmpFont;
                    text.SetAllDirty();
                    fontReplaced++;
                }
                else if (_replacementTmpFont != null && IsTargetFont(text.font.name))
                {
                    fontCandidates++;
                    text.font = _replacementTmpFont;
                    text.SetAllDirty();
                    fontReplaced++;
                }
            }

            string? value = text.text;
            if (Plugin.EnableTextOverrides.Value
                && Plugin.EnableTextOverrideScan.Value
                && TryGetOverride(value, out string? replacement))
            {
                text.text = replacement;
                text.SetAllDirty();
                overridesApplied++;
                continue;
            }

            CollectChineseText(value);
        }

        if (fontReplaced != _lastTmpTextReplaced || fontCandidates != _lastTmpTextCandidates)
        {
            _lastTmpTextReplaced = fontReplaced;
            _lastTmpTextCandidates = fontCandidates;
            Plugin.PluginLog.LogInfo($"TMP Text font candidates={fontCandidates}, replaced={fontReplaced}");
        }

        if (overridesApplied != _lastTmpOverridesApplied)
        {
            _lastTmpOverridesApplied = overridesApplied;
            Plugin.PluginLog.LogInfo($"TMP Text overrides applied={overridesApplied}");
        }
    }

    private TMP_FontAsset? ResolveAlibabaReplacementTmpFont()
    {
        if (_alibabaReplacementTmpFont != null)
        {
            return _alibabaReplacementTmpFont;
        }

        var fontAssets = Resources.FindObjectsOfTypeAll<TMP_FontAsset>();
        foreach (var fontAsset in fontAssets)
        {
            if (fontAsset == null || string.IsNullOrWhiteSpace(fontAsset.name))
            {
                continue;
            }

            if (fontAsset.name.Equals(AlibabaReplacementTmpFontName, StringComparison.OrdinalIgnoreCase))
            {
                _alibabaReplacementTmpFont = fontAsset;
                Plugin.PluginLog.LogInfo($"Alibaba TMP font mapped for SourceHan replacement: {fontAsset.name}");
                return _alibabaReplacementTmpFont;
            }
        }

        foreach (var fontAsset in fontAssets)
        {
            if (fontAsset == null || string.IsNullOrWhiteSpace(fontAsset.name))
            {
                continue;
            }

            if (fontAsset.name.IndexOf("AlibabaPuHuiTi-Regular", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                _alibabaReplacementTmpFont = fontAsset;
                Plugin.PluginLog.LogInfo($"Alibaba TMP font mapped for SourceHan replacement: {fontAsset.name}");
                return _alibabaReplacementTmpFont;
            }
        }

        if (!_loggedMissingAlibabaTmpFont)
        {
            _loggedMissingAlibabaTmpFont = true;
            Plugin.PluginLog.LogWarning($"Alibaba TMP font not found yet: {AlibabaReplacementTmpFontName}");
        }

        return null;
    }

    private void LoadTextOverrides()
    {
        _overridePath = Path.Combine(Paths.PluginPath, "HXSS.HuiWenFontReplacer", OverrideFileName);
        if (!File.Exists(_overridePath))
        {
            Plugin.PluginLog.LogInfo($"Text override file not found. Skipped: {_overridePath}");
            return;
        }

        int loaded = 0;
        _textOverrides.Clear();
        _overrideLastWriteUtc = File.GetLastWriteTimeUtc(_overridePath);
        foreach (string rawLine in File.ReadAllLines(_overridePath, Encoding.UTF8))
        {
            string line = rawLine.TrimEnd('\r', '\n');
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#", StringComparison.Ordinal))
            {
                continue;
            }

            string[] parts = line.Split('\t');
            if (parts.Length < 2)
            {
                continue;
            }

            string source = DecodeEscapes(parts[0].Trim());
            string target = DecodeEscapes(parts[1].Trim());
            if (source.Length == 0 || target.Length == 0)
            {
                continue;
            }

            AddTextOverrideVariants(source, target);
            loaded++;
        }

        Plugin.PluginLog.LogInfo($"Text overrides loaded: {loaded}");
    }

    private void AddTextOverrideVariants(string source, string target)
    {
        _textOverrides[source] = target;

        string repairedSource = RepairUtf8Mojibake(source);
        string repairedTarget = RepairUtf8Mojibake(target);
        if (!string.Equals(repairedSource, source, StringComparison.Ordinal)
            || !string.Equals(repairedTarget, target, StringComparison.Ordinal))
        {
            _textOverrides[repairedSource] = repairedTarget;
        }
    }

    private void ReloadTextOverridesIfChanged()
    {
        if (_overridePath == null || !File.Exists(_overridePath))
        {
            return;
        }

        DateTime currentWriteUtc = File.GetLastWriteTimeUtc(_overridePath);
        if (currentWriteUtc == _overrideLastWriteUtc)
        {
            return;
        }

        LoadTextOverrides();
    }

    private void LoadCollectorCache()
    {
        string pluginDir = Path.Combine(Paths.PluginPath, "HXSS.HuiWenFontReplacer");
        Directory.CreateDirectory(pluginDir);
        _collectorPath = Path.Combine(pluginDir, CollectorFileName);

        if (!File.Exists(_collectorPath))
        {
            File.WriteAllText(_collectorPath, "source\tfirst_seen_unix\n", new UTF8Encoding(false));
            return;
        }

        foreach (string rawLine in File.ReadAllLines(_collectorPath, Encoding.UTF8))
        {
            if (string.IsNullOrWhiteSpace(rawLine) || rawLine.StartsWith("source\t", StringComparison.Ordinal))
            {
                continue;
            }

            string source = rawLine.Split('\t')[0];
            if (source.Length > 0)
            {
                _collectedChinese.Add(source);
            }
        }
    }

    private bool TryGetOverride(string? source, out string? replacement)
    {
        replacement = null;
        if (string.IsNullOrEmpty(source))
        {
            return false;
        }

        if (_textOverrides.TryGetValue(source, out replacement))
        {
            return true;
        }

        string normalized = source.Trim();
        return normalized.Length != source.Length
            && _textOverrides.TryGetValue(normalized, out replacement);
    }

    private void CollectChineseText(string? value)
    {
        if (!_koreanUiActiveForCollection
            || string.IsNullOrWhiteSpace(value)
            || !ContainsChinese(value)
            || ContainsHangul(value)
            || _collectedChinese.Contains(value))
        {
            return;
        }

        _collectedChinese.Add(value);
        if (_collectorPath == null)
        {
            return;
        }

        try
        {
            string line = EscapeForTsv(value) + "\t" + DateTimeOffset.UtcNow.ToUnixTimeSeconds() + Environment.NewLine;
            File.AppendAllText(_collectorPath, line, new UTF8Encoding(false));
        }
        catch (Exception ex)
        {
            Plugin.PluginLog.LogWarning($"Failed to collect Chinese text: {ex.Message}");
        }
    }
    private bool HasKoreanTitleStartText()
    {
        var uiTexts = Resources.FindObjectsOfTypeAll<UnityEngine.UI.Text>();
        foreach (var text in uiTexts)
        {
            if (text != null && IsKoreanTitleStartText(text.text))
            {
                return true;
            }
        }

        var tmpTexts = Resources.FindObjectsOfTypeAll<TMP_Text>();
        foreach (var text in tmpTexts)
        {
            if (text != null && IsKoreanTitleStartText(text.text))
            {
                return true;
            }
        }

        return false;
    }

    private static bool IsKoreanTitleStartText(string? value)
    {
        if (string.IsNullOrWhiteSpace(value) || !ContainsHangul(value))
        {
            return false;
        }

        string normalized = value
            .Replace(" ", string.Empty, StringComparison.Ordinal)
            .Replace("\r", string.Empty, StringComparison.Ordinal)
            .Replace("\n", string.Empty, StringComparison.Ordinal)
            .Replace("\t", string.Empty, StringComparison.Ordinal);

        return normalized.Contains("게임시작", StringComparison.Ordinal)
            && (
                normalized.Contains("아무곳", StringComparison.Ordinal)
                || normalized.Contains("빈곳", StringComparison.Ordinal)
                || normalized.Contains("빈공간", StringComparison.Ordinal)
            )
            && (
                normalized.Contains("눌러", StringComparison.Ordinal)
                || normalized.Contains("클릭", StringComparison.Ordinal)
            );
    }

    private static bool IsLanguageSelectionText(string value)
    {
        return value.Equals("select language", StringComparison.OrdinalIgnoreCase)
            || value.Equals("选择语言", StringComparison.Ordinal)
            || value.Equals("選擇語言", StringComparison.Ordinal)
            || value.Equals("간체 중국어", StringComparison.Ordinal)
            || value.Equals("번체 중국어", StringComparison.Ordinal)
            || value.Equals("한국어", StringComparison.Ordinal)
            || value.Equals("일본어", StringComparison.Ordinal)
            || value.Equals("English", StringComparison.Ordinal)
            || value.Equals("Русский", StringComparison.Ordinal)
            || value.Equals("Deutsch", StringComparison.Ordinal)
            || value.Equals("Français", StringComparison.Ordinal)
            || value.Equals("ภาษาไทย", StringComparison.Ordinal)
            || value.Equals("Polski", StringComparison.Ordinal)
            || value.Equals("Türkçe", StringComparison.Ordinal)
            || value.Equals("Українська", StringComparison.Ordinal)
            || value.Equals("Italiano", StringComparison.Ordinal)
            || value.Equals("Čeština", StringComparison.Ordinal)
            || value.Equals("Magyar", StringComparison.Ordinal)
            || value.Equals("Nederlands", StringComparison.Ordinal)
            || value.StartsWith("Español", StringComparison.Ordinal)
            || value.StartsWith("Português", StringComparison.Ordinal)
            || value.Equals("Svenska", StringComparison.Ordinal)
            || value.Equals("Dansk", StringComparison.Ordinal);
    }

    private static bool ContainsChinese(string value)
    {
        foreach (char c in value)
        {
            if (c >= '\u4e00' && c <= '\u9fff')
            {
                return true;
            }
        }

        return false;
    }

    private static bool ContainsHangul(string value)
    {
        foreach (char c in value)
        {
            if ((c >= '\uac00' && c <= '\ud7a3') || (c >= '\u3130' && c <= '\u318f'))
            {
                return true;
            }
        }

        return false;
    }

    private static string DecodeEscapes(string value)
    {
        return value
            .Replace("\\t", "\t", StringComparison.Ordinal)
            .Replace("\\n", "\n", StringComparison.Ordinal)
            .Replace("\\r", "\r", StringComparison.Ordinal);
    }

    private static string RepairUtf8Mojibake(string value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return value;
        }

        byte[] bytes = new byte[value.Length];
        for (int i = 0; i < value.Length; i++)
        {
            if (!TryMapWindows1252CharToByte(value[i], out byte b))
            {
                return value;
            }

            bytes[i] = b;
        }

        try
        {
            string repaired = Encoding.UTF8.GetString(bytes);
            return repaired.IndexOf('\uFFFD') >= 0 ? value : repaired;
        }
        catch
        {
            return value;
        }
    }

    private static bool TryMapWindows1252CharToByte(char c, out byte b)
    {
        if (c <= '\u007f' || (c >= '\u00a0' && c <= '\u00ff'))
        {
            b = (byte)c;
            return true;
        }

        switch (c)
        {
            case '\u20ac': b = 0x80; return true;
            case '\u201a': b = 0x82; return true;
            case '\u0192': b = 0x83; return true;
            case '\u201e': b = 0x84; return true;
            case '\u2026': b = 0x85; return true;
            case '\u2020': b = 0x86; return true;
            case '\u2021': b = 0x87; return true;
            case '\u02c6': b = 0x88; return true;
            case '\u2030': b = 0x89; return true;
            case '\u0160': b = 0x8a; return true;
            case '\u2039': b = 0x8b; return true;
            case '\u0152': b = 0x8c; return true;
            case '\u017d': b = 0x8e; return true;
            case '\u2018': b = 0x91; return true;
            case '\u2019': b = 0x92; return true;
            case '\u201c': b = 0x93; return true;
            case '\u201d': b = 0x94; return true;
            case '\u2022': b = 0x95; return true;
            case '\u2013': b = 0x96; return true;
            case '\u2014': b = 0x97; return true;
            case '\u02dc': b = 0x98; return true;
            case '\u2122': b = 0x99; return true;
            case '\u0161': b = 0x9a; return true;
            case '\u203a': b = 0x9b; return true;
            case '\u0153': b = 0x9c; return true;
            case '\u017e': b = 0x9e; return true;
            case '\u0178': b = 0x9f; return true;
            default:
                b = 0;
                return false;
        }
    }

    private static string EscapeForTsv(string value)
    {
        return value
            .Replace("\r", "\\r", StringComparison.Ordinal)
            .Replace("\n", "\\n", StringComparison.Ordinal)
            .Replace("\t", "\\t", StringComparison.Ordinal);
    }

    private static bool IsTargetFont(string? fontName)
    {
        return !string.IsNullOrWhiteSpace(fontName)
            && (
                fontName.IndexOf(TargetFontName, StringComparison.OrdinalIgnoreCase) >= 0
                || fontName.IndexOf("HuiWen", StringComparison.OrdinalIgnoreCase) >= 0
                || fontName.IndexOf("ZhengKai", StringComparison.OrdinalIgnoreCase) >= 0
                || fontName.IndexOf("FZXZTFW", StringComparison.OrdinalIgnoreCase) >= 0
            );
    }

    private static bool IsSourceHanFont(string? fontName)
    {
        return !string.IsNullOrWhiteSpace(fontName)
            && fontName.IndexOf(SourceHanFontName, StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private void LogFontDebug(string kind, string fontName, string objectPath, string? value)
    {
        if (string.IsNullOrWhiteSpace(_fontDebugPath) || string.IsNullOrWhiteSpace(value))
        {
            return;
        }

        if (!ContainsHangul(value) && value.IndexOf('\u25a1') < 0)
        {
            return;
        }

        string key = $"{kind}\t{fontName}\t{objectPath}\t{value}";
        if (!_fontDebugEntries.Add(key))
        {
            return;
        }

        try
        {
            File.AppendAllText(
                _fontDebugPath,
                $"{kind}\t{EscapeForTsv(fontName)}\t{EscapeForTsv(objectPath)}\t{EscapeForTsv(value)}\n",
                Encoding.UTF8);
        }
        catch (Exception ex)
        {
            Plugin.PluginLog.LogWarning($"Failed to write font debug row: {ex.Message}");
        }
    }

    private static string GetGameObjectPath(GameObject? gameObject)
    {
        if (gameObject == null)
        {
            return string.Empty;
        }

        List<string> names = new();
        Transform? current = gameObject.transform;
        while (current != null)
        {
            names.Add(current.name);
            current = current.parent;
        }

        names.Reverse();
        return string.Join("/", names);
    }

}
