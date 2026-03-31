def get_cookie_from_browser(browser_choice: str, domain: str = "") -> dict[str, str]:
    if not browser_choice or not domain:
        return {}

    try:
        import browser_cookie3
    except ImportError as exc:
        raise RuntimeError("browser_cookie3 is required for browser cookie extraction") from exc

    browser_functions = {
        "chrome": browser_cookie3.chrome,
        "firefox": browser_cookie3.firefox,
        "edge": browser_cookie3.edge,
        "opera": browser_cookie3.opera,
        "opera_gx": browser_cookie3.opera_gx,
        "safari": browser_cookie3.safari,
        "chromium": browser_cookie3.chromium,
        "brave": browser_cookie3.brave,
        "vivaldi": browser_cookie3.vivaldi,
        "librewolf": browser_cookie3.librewolf,
    }
    cookie_jar = browser_functions[browser_choice](domain_name=domain)
    return {cookie.name: cookie.value for cookie in cookie_jar if cookie.domain.endswith(domain)}
