# SPDX-License-Identifier: MPL-2.0
# Adapted from upstream docker/from-source/Ubuntu, cp-26.04.6-1.
# Modified by Software GestiónPYME, 2026-11-12: own branding, UID and health probe.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpng16-16t64 fontconfig adduser cpio tzdata findutils libcap2-bin openssl \
    libpam0g libxcb-shm0 libxcb-render0 libxrender1 libxext6 \
    fonts-wqy-zenhei fonts-wqy-microhei fonts-droid-fallback fonts-noto-cjk ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY instdir/ /
RUN groupadd --gid 1001 cool && useradd --uid 1001 --gid 1001 --home-dir /opt/cool --no-create-home cool \
    && mkdir -p /opt/cool/child-roots /opt/cool/cache \
    && setcap cap_fowner,cap_chown,cap_sys_chroot=ep /usr/bin/coolforkit-caps \
    && setcap cap_sys_admin=ep /usr/bin/coolmount \
    && coolwsd-systemplate-setup /opt/cool/systemplate /opt/collaboraoffice \
    && touch /var/log/coolwsd.log \
    && chown cool:cool /var/log/coolwsd.log \
    && chown -R cool:cool /opt/cool /etc/coolwsd \
    && chmod g+w /etc/passwd
EXPOSE 9980
USER 1001
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 CMD ["/usr/bin/coolwsd", "--probe", "--use-env-vars"]
ENTRYPOINT ["/usr/bin/coolwsd", "--use-env-vars", "--o:sys_template_path=/opt/cool/systemplate", "--o:child_root_path=/opt/cool/child-roots", "--o:file_server_root_path=/usr/share/coolwsd", "--o:cache_files.path=/opt/cool/cache", "--o:logging.color=false", "--o:stop_on_config_change=true"]
