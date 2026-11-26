const release = "https://github.com/sgshiv001/TRADE-VELOCITY/releases";
export const releaseVersion = "2.0.1";
export const releaseNotes = `${release}/tag/v${releaseVersion}`;
const downloads = `${release}/download/v${releaseVersion}`;
export const releaseChecksums = `${downloads}/SHA256SUMS.txt`;

export const releases = [
  {
    platform: "Windows",
    description: "Run the portable app to open the live trading workspace.",
    files: [{
      label: "Download Windows EXE",
      requirements: "Windows x64 · Unsigned preview",
      href: `${downloads}/TradeVelocity-Trader.exe`,
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
    description: "Install the debug-signed Android demo build.",
    files: [{
      label: "Download Android APK",
      requirements: "Android 7 or later · ARM64 and x86-64",
      href: `${downloads}/TradeVelocity-Android.apk`,
    }],
  },
] as const;
