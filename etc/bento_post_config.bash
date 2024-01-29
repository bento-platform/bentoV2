#!/usr/bin/env bash

echo "BENTO_GATEWAY_USE_TLS = $BENTO_GATEWAY_USE_TLS"

if [[ "$BENTO_GATEWAY_USE_TLS" == 'true' || "$BENTO_GATEWAY_USE_TLS" == '1' ]]; then
  KC_PROXY='none'
  KC_HOSTNAME_STRICT='true'
  KC_HOSTNAME_STRICT_HTTPS='true'
  KC_HTTP_ENABLED='false'
  KC_HTTPS_CERTIFICATE_FILE=/run/secrets/keycloak-cert-file
  KC_HTTPS_CERTIFICATE_KEY_FILE=/run/secrets/keycloak-cert-key-file
else
  # Disable TLS in keycloak
  KC_PROXY='passthrough'
  KC_HOSTNAME_STRICT='false'
  KC_HOSTNAME_STRICT_HTTPS='false'
  KC_HTTP_ENABLED='true'
fi
