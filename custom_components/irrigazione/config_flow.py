"""Config flow per l'integrazione Irrigazione."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4

STEP_USER_SCHEMA = vol.Schema(
    {vol.Required("title", default="Irrigazione"): str}
)


def _zone_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ZONA_1, default=defaults.get(CONF_ZONA_1, "")): selector.selector(
                {"entity": {"domain": "switch"}}
            ),
            vol.Required(CONF_ZONA_2, default=defaults.get(CONF_ZONA_2, "")): selector.selector(
                {"entity": {"domain": "switch"}}
            ),
            vol.Required(CONF_ZONA_3, default=defaults.get(CONF_ZONA_3, "")): selector.selector(
                {"entity": {"domain": "switch"}}
            ),
            vol.Required(CONF_ZONA_4, default=defaults.get(CONF_ZONA_4, "")): selector.selector(
                {"entity": {"domain": "switch"}}
            ),
        }
    )


class IrrigazioneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wizard di configurazione iniziale."""

    VERSION = 1
    _title: str = "Irrigazione"

    async def async_step_user(self, user_input: dict | None = None):
        if user_input is not None:
            self._title = user_input["title"]
            return await self.async_step_zone()
        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

    async def async_step_zone(self, user_input: dict | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            for key in [CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4]:
                entity_id = user_input.get(key, "")
                if entity_id and not self.hass.states.get(entity_id):
                    errors[key] = "entity_not_found"
            if not errors:
                return self.async_create_entry(title=self._title, data=user_input)
        return self.async_show_form(
            step_id="zone",
            data_schema=_zone_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return IrrigazioneOptionsFlow(config_entry)


class IrrigazioneOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            for key in [CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4]:
                entity_id = user_input.get(key, "")
                if entity_id and not self.hass.states.get(entity_id):
                    errors[key] = "entity_not_found"
            if not errors:
                return self.async_create_entry(title="", data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_zone_schema(current),
            errors=errors,
        )
