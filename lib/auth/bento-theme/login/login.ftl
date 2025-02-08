<!DOCTYPE html>
<html <#if realm.internationalizationEnabled> lang="${locale.currentLanguageTag}"</#if>>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${msg("login.description")}">
    <title>${msg("login.title")}</title>
    <link rel="stylesheet" href="${url.resourcesPath}/css/styles.css">
</head>
<body>
    <div class="background">
        <div class="login-container">
            <#if realm.internationalizationEnabled && locale.supported?size gt 1>
                <div class="language-switcher">
                    <select
                            aria-label="${msg("languages")}"
                            id="login-select-toggle"
                            onchange="if (this.value) window.location.href=this.value">
                        <#list locale.supported?sort_by("label") as l>
                            <option
                                    value="${l.url}"
                                    ${(l.languageTag == locale.currentLanguageTag)?then('selected','')}>
                                ${l.label}
                            </option>
                        </#list>
                    </select>
                </div>
            </#if>

            <img src="${url.resourcesPath}/img/branding.png" alt="${msg("login.logo.alt")}" class="logo" />

            <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post" aria-labelledby="login-heading">
                <h1 id="login-heading">${msg("login.heading")}</h1>

                <#-- Username Field -->
                <div class="row">
                    <div class="col-label">
                        <label for="username" class="form-label">${msg("login.username.label")}</label>
                    </div>
                    <div class="col-input">
                        <input id="username" class="form-input" type="text" name="username" placeholder="${msg("login.username.placeholder")}" value="${(login.username!'')}" autofocus required
                            aria-invalid="<#if messagesPerField.existsError('username')>true</#if>" />
                        <#if messagesPerField.existsError('username')>
                            <span id="input-error" class="error-message">${kcSanitize(messagesPerField.getFirstError('username'))?no_esc}</span>
                        </#if>
                    </div>
                </div>

                <#-- Password Field -->
                <div class="row">
                    <div class="col-label">
                        <label for="password" class="form-label">${msg("login.password.label")}</label>
                    </div>
                    <div class="col-input">
                        <div class="password-container">
                            <input id="password" class="form-input" type="password" name="password" placeholder="${msg("login.password.placeholder")}" required
                                aria-invalid="<#if messagesPerField.existsError('password')>true</#if>" />
                            <button type="button" class="toggle-password" aria-label="${msg("login.password.toggle.aria")}" onclick="togglePasswordVisibility()">
                               <img src="${url.resourcesPath}/img/visibility_off.svg" width="24" height="24"  alt="Show password"/>
                            </button>
                        </div>
                        <#if messagesPerField.existsError('password')>
                            <span id="input-error" class="error-message">${kcSanitize(messagesPerField.getFirstError('password'))?no_esc}</span>
                        </#if>
                    </div>
                </div>

                <#-- Submit Button -->
                <div class="row">
                    <button type="submit" class="btn-submit" name="login" value="${msg("login.button.submit")}">${msg("login.button.submit")}</button>
                </div>

                <#-- Ghost Button -->
                <div class="ghost-watermark">
                    <img src="${url.resourcesPath}/img/Bento_logo_blk.png" class="ghost-image" />
                </div>
            </form>
        </div>
    </div>

    <script>
        function togglePasswordVisibility() {
            const passwordField = document.getElementById('password');
            const toggleButton = document.querySelector('.toggle-password img');
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                toggleButton.src = `${url.resourcesPath}/img/visibility_off.svg`;
                toggleButton.alt = '${msg("login.password.toggle.hide.alt")}';
            } else {
                passwordField.type = 'password';
                toggleButton.src = `${url.resourcesPath}/img/visibility_on.svg`;
                toggleButton.alt = '${msg("login.password.toggle.alt")}';
            }
        }
    </script>
</body>
</html>
