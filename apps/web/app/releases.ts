export const releases = [
  {
    platform: "Windows", version: "1.0.0", date: "23 November 2026", kind: "Legacy release",
    requirements: "Windows x64 · Portable EXE", bytes: 24060954,
    href: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v1.0.0/TradeVelocity.exe",
    checksum: "e34f2642db4e278f0344479db9d52105c6f90caeaa51aac339a7d32965b8980c",
    notes: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v1.0.0",
  },
  {
    platform: "Android", version: "1.1.0", date: "25 November 2026", kind: "Legacy test build",
    requirements: "Android · APK", bytes: 4461974,
    href: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v1.1.0-android-test/TradeVelocity-Android-test.apk",
    checksum: "301497c363c555a7c302e2c2724c6cb59899ead420d591c74c891d775d630947",
    notes: "https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v1.1.0-android-test",
  },
] as const;
