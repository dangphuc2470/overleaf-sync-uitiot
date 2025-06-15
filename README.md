# Overleaf-Sync (UIT LaTeX Support)
### Easy Overleaf Two-Way Synchronization with UIT LaTeX Support

![Made In Austria](https://img.shields.io/badge/Made%20in-Austria-%23ED2939.svg) ![PyPI - License](https://img.shields.io/pypi/l/overleaf-sync.svg) ![PyPI](https://img.shields.io/pypi/v/overleaf-sync.svg) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/overleaf-sync.svg)

**This is a fork of the original [overleaf-sync](https://github.com/moritzgloeckl/overleaf-sync) project with added support for UIT LaTeX (latex.uitiot.vn).**

This tool provides an easy way to synchronize Overleaf projects from and to your local computer. No paid account necessary.

### 🆕 New Features (UIT LaTeX Fork)
- **Full support for UIT LaTeX** (latex.uitiot.vn)
- **Keep browser open option** during login with `--keep-browser` flag
- **Improved cookie handling** for different Overleaf instances
- **Better error handling** and debugging output
- **Auto-detection** of different meta tag formats

----

## Features
- Sync your locally modified `.tex` (and other) files to your Overleaf projects
- Sync your remotely modified `.tex` (and other) files to computer
- **Works with UIT LaTeX (latex.uitiot.vn) and standard Overleaf**
- Works with free account
- No Git or Dropbox required
- Does not steal or store your login credentials (works with a persisted cookie, logging in is done on the original website)

## How To Use
### Install
Clone this repository and install locally:

```bash
git clone https://github.com/your-username/overleaf-sync-master.git
cd overleaf-sync-master
pip install -e .
```

Or install the dependencies directly:
```bash
pip install -r requirements.txt
```

### Prerequisites
- Create your project on [UIT LaTeX](https://latex.uitiot.vn/project), for example a project named `test`. Overleaf-sync is not able to create projects (yet).
- Create a folder, preferably with the same name as the project (`test`) on your computer.
- Execute the script from that folder (`test`).
- If you do not specify the project name, overleaf-sync uses the current folder's name as the project name.

### Usage
#### Login
```bash
# Standard login (browser closes automatically after login)
ols login [--path]

# Keep browser open after login (new feature!)
ols login --keep-browser [--path]
```

Logging in will be handled by a mini web browser opening on your device (using Qt5). You can then enter your username and password securely on the official UIT LaTeX website. You might get asked to solve a CAPTCHA in the process. Your credentials are sent to UIT LaTeX over HTTPS.

With the `--keep-browser` option, the browser window will remain open after successful login, allowing you to continue browsing or verify your login.

It then stores your *cookie* (**not** your login credentials) in a hidden file called `.olauth` in the same folder you run the command from. It is possible to store the cookie elsewhere using the `--path` option. The cookie file will not be synced to or from UIT LaTeX.

Keep the `.olauth` file save, as it can be used to log in into your account.

### Listing all projects
```bash
ols list [--store-path -v/--verbose]
# Output example:
# 06/15/2025, 03:34:17 - KLTN-24.2-DuyNT-PhucDNH
# 06/14/2025, 18:31:55 - HỆ THỐNG MẠNG LƯỚI ĐIỀU KHIỂN ĐÈN GIAO THÔNG...
```

Use `ols list` to conveniently list all projects in your account available for syncing. 

### Downloading project's PDF
```bash
ols download [--name --download-path --store-path -v/--verbose]
```

Use `ols download` to compile and download your project's PDF. Specify a download path if you do not want to store the PDF file in the current folder. Currently only downloads the first PDF file it finds.

### Syncing
```bash
ols [-l/--local-only -r/--remote-only --store-path -p/--path -i/--olignore]
```

Just calling `ols` will two-way sync your project. When there are changes both locally, and remotely you will be asked which file to keep. Using the `-l` or `-r` option you can specify to either sync local project files to UIT LaTeX only or UIT LaTeX files to local ones only respectively. When using these options you can also sync deleted files. If a file has been deleted it can either be deleted on the target (remote when `-l`, local when `-r`) as well, restored on the source (local when `-l`, remote when `-r`) or ignored.

The option `--store-path` specifies the path of the cookie file created by the `login` command. If you did not change its path, you do not need to specify this argument. The `-p/--path` option allows you to specify a different sync folder than the one you're calling `ols` from. The `-i/--olignore` option allows you to specify the path of an `.olignore` file. It uses `fnmatch` internally, so it may have some similarity to `.gitignore` but doesn't work exactly the same. For example, if you wish to exclude a specific folder named `out`, you need to specify it as `out/*`. See [here](https://docs.python.org/3/library/fnmatch.html) for more information.

Sample Output:

```
Project queried successfully.
✅  Querying project
Project downloaded successfully.
✅  Downloading project

Syncing files from remote to local
====================

[SYNCING] report.tex
report.tex does not exist on local. Creating file.

[SYNCING] other-report.tex
other-report.tex does not exist on local. Creating file.


✅  Syncing files from remote to local
```

## UIT LaTeX Specific Notes

This fork includes specific enhancements for UIT LaTeX (latex.uitiot.vn):

- **Cookie Format**: Supports `overleaf.sid` cookies used by UIT LaTeX
- **Meta Tag Detection**: Auto-detects `ol-prefetchedProjectsBlob` format used by newer UIT LaTeX versions
- **Authentication Flow**: Handles UIT LaTeX's OAuth flow with Google authentication
- **Debug Output**: Improved error messages and debug information for troubleshooting

## Known Bugs
- When modifying a file on UIT LaTeX and immediately syncing afterwards, the tool might not detect the changes. Please allow 1-2 minutes after modifying a file on UIT LaTeX before syncing it to your local computer.

## Contributing

All pull requests and change/feature requests are welcome.

## Credits

This project is a fork of the original [overleaf-sync](https://github.com/moritzgloeckl/overleaf-sync) by [Moritz Glöckl](https://github.com/moritzglk). 

**Original Project**: https://github.com/moritzgloeckl/overleaf-sync

Modifications made for UIT LaTeX support include cookie handling improvements, meta tag detection, and browser control enhancements.

## Disclaimer
THE AUTHOR OF THIS SOFTWARE AND THIS SOFTWARE IS NOT ENDORSED BY, DIRECTLY AFFILIATED WITH, MAINTAINED, AUTHORIZED, OR SPONSORED BY OVERLEAF, WRITELATEX LIMITED, OR UIT (UNIVERSITY OF INFORMATION TECHNOLOGY). ALL PRODUCT AND COMPANY NAMES ARE THE REGISTERED TRADEMARKS OF THEIR ORIGINAL OWNERS. THE USE OF ANY TRADE NAME OR TRADEMARK IS FOR IDENTIFICATION AND REFERENCE PURPOSES ONLY AND DOES NOT IMPLY ANY ASSOCIATION WITH THE TRADEMARK HOLDER OF THEIR PRODUCT BRAND.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

THIS SOFTWARE WAS DESIGNED TO BE USED ONLY FOR RESEARCH PURPOSES. THIS SOFTWARE COMES WITH NO WARRANTIES OF ANY KIND WHATSOEVER. USE IT AT YOUR OWN RISK! IF THESE TERMS ARE NOT ACCEPTABLE, YOU AREN'T ALLOWED TO USE THE CODE.

