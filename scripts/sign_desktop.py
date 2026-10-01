"""Optional Windows certificate-store signing; no certificates are purchased.

Use --dry-run to inspect the planned commands. Private keys/passwords are never
passed as command-line arguments or stored in the repository.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def commands(executable, thumbprint, timestamp_url, signtool="signtool.exe"):
    executable = Path(executable).resolve()
    if not executable.is_relative_to((ROOT / "dist").resolve()) or executable.suffix.lower() != ".exe":
        raise ValueError("Sign only this project's explicitly selected generated EXE inside dist")
    if not executable.is_file():
        raise ValueError("Build the executable before signing")
    if not re.fullmatch(r"[a-fA-F0-9]{40}",thumbprint):
        raise ValueError("Provide the exact 40-hex certificate-store thumbprint")
    parsed = urlsplit(timestamp_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Provide an HTTPS RFC3161 timestamp URL")
    return ([str(signtool),"sign","/sha1",thumbprint,"/fd","SHA256","/tr",timestamp_url,"/td","SHA256",str(executable)],
            [str(signtool),"verify","/pa","/all","/v",str(executable)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe",type=Path,default=ROOT / "dist/TradeVelocity/TradeVelocity.exe")
    parser.add_argument("--certificate-thumbprint",required=True)
    parser.add_argument("--timestamp-url",required=True)
    parser.add_argument("--signtool",default="signtool.exe")
    parser.add_argument("--dry-run",action="store_true")
    args = parser.parse_args()
    try:
        sign,verify = commands(args.exe,args.certificate_thumbprint,args.timestamp_url,args.signtool)
        if args.dry_run:
            print("Planned commands only; nothing will be signed:")
            print(subprocess.list2cmdline(sign)); print(subprocess.list2cmdline(verify))
            return
        tool = shutil.which(args.signtool)
        if not tool:
            raise ValueError("Microsoft SignTool is missing. Install the Windows SDK signing tools yourself; see docs/windows-release.md")
        sign[0] = verify[0] = tool
        subprocess.run(sign,check=True)
        subprocess.run(verify,check=True)
        print("Signature verified. Repackage the ZIP and regenerate hashes after signing; rebuilding invalidates the signature.")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
