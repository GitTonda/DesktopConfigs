// ==============================================================================
// Zen Browser Custom Preferences (Catppuccin Mocha + 0px Square Aesthetics)
// ==============================================================================

// Enable userChrome.css and userContent.css stylesheets
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
user_pref("svg.context-properties.content.enabled", true);
user_pref("layout.css.prefers-color-scheme.content-override", 0);

// Square borders and compact layout
user_pref("zen.theme.border-radius", 0);
user_pref("zen.theme.content-element-separation", 0);
user_pref("zen.theme.accent-color", "#2977af");
user_pref("zen.welcome-screen.seen", true);
user_pref("browser.tabs.firefox-view", false);
user_pref("browser.toolbars.bookmarks.visibility", "always");

// Force Dark Mode for all web content and browser UI
user_pref("browser.theme.content-theme", 0);
user_pref("browser.theme.toolbar-theme", 0);
user_pref("browser.in-content.dark-mode", true);
user_pref("ui.systemUsesDarkTheme", 1);

// Automatic extension loading from profile extensions directory
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 15);
