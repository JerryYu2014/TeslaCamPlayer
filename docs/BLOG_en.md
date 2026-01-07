## Tesla dashcam video player built on Python and PyQt5

GitHub repository: https://github.com/JerryYu2014/TeslaCamPlayer

The first time many Tesla owners open the `TeslaCam` folder on their USB drive, the reaction is usually the same:

- The folder structure is deep and confusing – `RecentClips`, `SavedClips`, and `SentryClips` all mixed together.
- Every moment is split into four separate files (front / rear / left / right), so watching a single event means hopping between players.
- When you need to export a clip for insurance, the police, or just to share with friends, you end up manually cutting and merging videos.

**TeslaCam Player** was born to solve exactly these real-world problems. It is a desktop application designed specifically for TeslaCam / Sentry Mode footage, turning raw files into a timeline-like browsing and management experience.

This post walks you through:

- Why a dedicated TeslaCam player is useful
- The core features of TeslaCam Player
- Real-world usage examples
- Installation and update workflow
- How to get involved and shape the future of the project

---

### Why do you need a dedicated TeslaCam player?

Tesla does not provide an official desktop tool for managing TeslaCam footage. Instead, it simply stores raw video files on your USB drive, in a structure similar to this:

```text
TeslaCam/
  ├─ RecentClips/
  ├─ SavedClips/
  └─ SentryClips/
        └─ 2025-01-01_12-00-00/
             ├─ 2025-01-01_12-00-00-front.mp4
             ├─ 2025-01-01_12-00-00-left_repeater.mp4
             ├─ 2025-01-01_12-00-00-right_repeater.mp4
             └─ 2025-01-01_12-00-00-back.mp4
```

This leads to a few obvious pain points:

- **Not intuitive** – you see a bunch of video files, not human-readable "events".
- **Hard to preview** – you have to open multiple players and switch between camera angles.
- **Difficult to manage and back up** – there is no unified list, filter, or tagging mechanism. Finding "that one incident" or "that beautiful road trip" can be painful.

TeslaCam Player aims to flip this around: instead of a file-centric view for machines, it provides an event-centric view for humans.

---

### Core features of TeslaCam Player

#### 1. Synchronized multi-camera playback

TeslaCam Player automatically groups front/rear/left/right camera files from the same timestamp into a single event, and shows them together:

- Preview multiple camera angles at once.
- One set of playback controls – seeking affects all views in sync.
- Quickly understand what happened around the car from every angle.

#### 2. Event list and filtering

The app scans a chosen TeslaCam folder and organizes footage into a browsable list by time and type (driving / sentry):

- Sorted by date and time.
- Grouped by source folder (`RecentClips`, `SavedClips`, `SentryClips`).
- Select any event to instantly preview all related camera feeds.

#### 3. Merge & export: one click to shareable video

When you need to submit footage to insurance, the police, or share online, manual editing is the last thing you want to do.

With TeslaCam Player you can:

- Right-click an event to open the **Merge & Export** dialog.
- Choose which camera views to include.
- Export a single combined video file with one click.

The exported file is ready to share with friends, upload to cloud storage, or attach as evidence.

#### 4. Clean UI with language support

The current version ships with a clean, focused UI and:

- **Bilingual interface (Chinese / English)** – auto-detects system language by default, and you can switch manually under `Settings → Language`.
- Remembers window size/position and last opened TeslaCam folder so you can pick up where you left off.
- Optional notification settings including system notifications, email, and WeCom bot integration for important events such as export completion.

#### 5. Built-in update checks

TeslaCam Player integrates with GitHub Releases for updates:

- Use `Help → Check for Updates` to query the latest version.
- If a new release is available, you will see a dialog with version details.
- You can download and start the installer directly from within the app.

The download happens in a separate, non-blocking dialog with:

- A progress bar and percentage display.
- The direct download URL (with a handy **Copy** button).
- The local save path (with an **Open Folder** button).
- Optional proxy settings just for update downloads, stored in your config file.
- Clean cancellation handling so closing the download dialog or clicking **Cancel** will stop the download without freezing or exiting the main application.

---

### Real-world use cases

#### Use case 1: Reviewing Sentry Mode alerts

You come back to your car and see a message on the screen: "Sentry Mode event detected".

With TeslaCam Player you can:

- Plug the TeslaCam USB drive into your computer.
- Open TeslaCam Player and jump to the Sentry events for that day.
- View front, rear, and side camera footage simultaneously to quickly determine whether it was a false alarm or someone actually approached your car.

#### Use case 2: Handling a minor collision

When a fender-bender or rear-end collision happens, clear video evidence is incredibly valuable.

With TeslaCam Player you can:

- Quickly locate the time of the incident in the event list.
- Review all angles to understand who was where and when.
- Use **Merge & Export** to generate a single video and send it straight to your insurer or the police.

#### Use case 3: Curating road trip memories

Many owners keep TeslaCam running during long drives, capturing beautiful scenery along the way.

TeslaCam Player helps you:

- Browse daily driving clips.
- Find the segments you like and export them in one click.
- Feed the exported videos into your favorite editor for a polished travel vlog.

---

### Installation and updates

TeslaCam Player is distributed via GitHub Releases.

- **On Windows**

  - Download the NSIS installer (`TeslaCamPlayer_x.y.z_Setup.exe`) from the Releases page.
  - Run the installer and launch TeslaCam Player from the Start menu.

- **On macOS**
  - Download the DMG (`TeslaCamPlayer-macOS-*.dmg`) for your architecture (Intel or Apple Silicon).
  - Drag the `.app` into your `Applications` folder.

In-app update checks make it easy to stay up to date without manually watching the repository.

---

### Open source and how to get involved

TeslaCam Player is an open-source project hosted on GitHub.

- You are free to download, use, and modify it.
- Bug reports, feature requests, and pull requests are all welcome.
- If you like the project, consider starring the repo or sharing it with other Tesla owners.

If there is a feature you would love to see – more layout options, tagging, smarter search, richer export templates – feel free to open an issue describing your idea, or submit a PR implementing it.

---

### Final thoughts

TeslaCam is a powerful built-in dashcam and surveillance system, but without the right tools, a lot of that data just sleeps on a USB drive.

**TeslaCam Player** has a simple mission:

> Make every recording easier to see, use, and share.

If you are a Tesla owner – or anyone who relies on dashcam footage – give TeslaCam Player a try, and let us know what you think. Your feedback will directly shape where the project goes next.
