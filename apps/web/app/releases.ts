export const releases = [
  {
    platform: "Windows", version: "0.3.4", date: "28 October 2026", kind: "Legacy release", format: "ZIP",
    requirements: "Windows x64 · Portable ZIP", bytes: 120503382,
    href: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v0.3.4/TradeVelocity-Windows-x64.zip",
    checksum: "50c6f9f6805cec5e5f48f568b9c3743a508cc4b9c0a89ff5d8b249b94524885e",
    notes: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v0.3.4",
  },
  {
    platform: "Android", version: "1.1.0", date: "25 November 2026", kind: "Legacy test build", format: "APK",
    requirements: "Android · APK", bytes: 4461974,
    href: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v1.1.0-android-test/TradeVelocity-Android-test.apk",
    checksum: "301497c363c555a7c302e2c2724c6cb59899ead420d591c74c891d775d630947",
    notes: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v1.1.0-android-test",
  },
] as const;
