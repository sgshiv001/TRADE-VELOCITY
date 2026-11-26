const release = "https://github.com/sgshiv001/TRADE-VELOCITY/releases";
const tag = "v2.0.0-beta.1-downloads";
const notes = `${release}/tag/${tag}`;
const downloads = `${release}/download/${tag}`;

export const releases = [
  {
    platform: "Windows",
    description: "Run the portable app to open the live trading workspace.",
    notes,
    files: [{
      label: "Download Windows EXE",
      requirements: "Windows x64 · Unsigned preview",
      bytes: 114750889,
      href: `${downloads}/TradeVelocity-Trader.exe`,
      checksum: "4c4b468df8e52ba2a70e9e8b00a0713db1448a39e24991a5d2d4f75b1835fb80",
    }],
  },
  {
    platform: "macOS",
    description: "Choose your Mac’s processor. Apple notarization is pending for these previews.",
    notes,
    files: [{
      label: "Download for Apple silicon",
      requirements: "Apple silicon · ZIP preview",
      bytes: 123463915,
      href: `${downloads}/TradeVelocity-macOS-arm64.zip`,
      checksum: "4851446ea9eedc93e28515f1d29f4ea014d404e9f13b440535c2d4b104187a63",
    }, {
      label: "Download for Intel Mac",
      requirements: "Intel Mac · ZIP preview",
      bytes: 129481414,
      href: `${downloads}/TradeVelocity-macOS-x64.zip`,
      checksum: "0b60814ceeaa916c281bc0da54d2f00e992fab6286b86f33cdf8f0ffdc5e44ff",
    }],
  },
  {
    platform: "Android",
    description: "Install the debug-signed 2.0 test build.",
    notes,
    files: [{
      label: "Download Android APK",
      requirements: "Android 7 or later · ARM64 and x86-64",
      bytes: 54172498,
      href: `${downloads}/TradeVelocity-Android.apk`,
      checksum: "8fa9dd6e41aaba18a5a0b0adbabf77c49b983bf6756e12b05c7119ff64c515dc",
    }],
  },
] as const;
