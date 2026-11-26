const release = "https://github.com/sgshiv001/TRADE-VELOCITY/releases";
export const releaseVersion = "2.0.2";
export const releaseNotes = `${release}/tag/v${releaseVersion}`;
const downloads = `${release}/download/v${releaseVersion}`;
export const releaseChecksums = `${downloads}/SHA256SUMS.txt`;
export const windowsVersion = "2.0.3";
const windowsDownloads = `${release}/download/windows-v${windowsVersion}`;
export const windowsChecksums = `${windowsDownloads}/SHA256SUMS.txt`;
export const androidVersion = "2.0.3";
const androidDownloads = `${release}/download/android-v${androidVersion}`;
export const androidChecksums = `${androidDownloads}/SHA256SUMS.txt`;

export const releases = [
  {
    platform: "Windows",
    description: "Install TradeVelocity and open it from Start. After browser approval, the desktop window comes forward and opens the workspace.",
    files: [{
      label: "Download Windows setup",
      requirements: "Windows x64 · Unsigned installer",
      href: `${windowsDownloads}/TradeVelocity-Setup-${windowsVersion}.exe`,
    }, {
      label: "Download portable EXE",
      requirements: "Windows x64 · Unsigned portable app",
      href: `${windowsDownloads}/TradeVelocity-Trader.exe`,
    }],
  },
  {
    platform: "macOS",
    description: "Choose your Mac’s processor. Apple notarization is pending for these previews.",
    files: [{
      label: "Download for Apple silicon",
      requirements: "Apple silicon · ZIP preview",
      href: `${downloads}/TradeVelocity-macOS-arm64.zip`,
    }, {
      label: "Download for Intel Mac",
      requirements: "Intel Mac · ZIP preview",
      href: `${downloads}/TradeVelocity-macOS-x64.zip`,
    }],
  },
  {
    platform: "Android",
    description: `Version ${androidVersion} includes native stock charts, a redesigned trade ticket, and the updated portfolio.`,
    files: [{
      label: "Download Android APK",
      requirements: "Android 7 or later · ARM64 and x86-64",
      href: `${androidDownloads}/TradeVelocity-Android.apk`,
    }],
  },
] as const;
