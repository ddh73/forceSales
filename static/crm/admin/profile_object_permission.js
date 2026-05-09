(function () {
    "use strict";

    function currentChangeUrl() {
        return window.location.pathname;
    }

    function lookupUrl() {
        const match = window.location.pathname.match(/^(.*\/crm\/profileobjectpermission\/)(?:add\/|[^/]+\/change\/)?$/);
        return match ? `${match[1]}lookup/` : null;
    }

    function setCheckbox(id, value) {
        const field = document.getElementById(id);
        if (field) {
            field.checked = Boolean(value);
        }
    }

    function updateCheckboxes(data) {
        setCheckbox("id_can_read", data.can_read);
        setCheckbox("id_can_write", data.can_write);
        setCheckbox("id_can_read_all", data.can_read_all);
        setCheckbox("id_can_edit_all", data.can_edit_all);
    }

    function lookupAccess() {
        const profile = document.getElementById("id_profile");
        const contentType = document.getElementById("id_content_type");
        if (!profile || !contentType || !profile.value || !contentType.value) {
            return;
        }

        const accessLookupUrl = lookupUrl();
        if (!accessLookupUrl) {
            return;
        }

        const params = new URLSearchParams({
            profile: profile.value,
            content_type: contentType.value,
        });

        fetch(`${accessLookupUrl}?${params.toString()}`, {
            credentials: "same-origin",
            headers: {"X-Requested-With": "XMLHttpRequest"},
        })
            .then((response) => response.ok ? response.json() : Promise.reject(response))
            .then((data) => {
                if (data.found && data.change_url && data.change_url !== currentChangeUrl()) {
                    window.location.assign(data.change_url);
                    return;
                }
                updateCheckboxes(data.found ? data : {
                    can_read: false,
                    can_write: false,
                    can_read_all: false,
                    can_edit_all: false,
                });
            })
            .catch(() => {});
    }

    document.addEventListener("DOMContentLoaded", function () {
        const profile = document.getElementById("id_profile");
        const contentType = document.getElementById("id_content_type");
        if (!profile || !contentType) {
            return;
        }
        profile.addEventListener("change", lookupAccess);
        contentType.addEventListener("change", lookupAccess);
    });
}());
