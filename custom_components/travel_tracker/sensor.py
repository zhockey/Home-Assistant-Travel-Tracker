"""Home Assistant entities for sanitized trip information."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity


SENSOR_NAMES = {
    "next_trip": ("Next Trip", "mdi:bag-suitcase"),
    "next_flight": ("Next Flight", "mdi:airplane"),
    "next_hotel": ("Next Hotel", "mdi:bed"),
    "next_rental_car": ("Next Rental Car", "mdi:car-key"),
    "days_until_trip": ("Days Until Trip", "mdi:calendar-clock"),
    "upcoming_trips": ("Upcoming Trips", "mdi:calendar-multiple"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        TravelSensor(coordinator, entry.entry_id, key, name, icon)
        for key, (name, icon) in SENSOR_NAMES.items()
    )


class TravelSensor(CoordinatorEntity, SensorEntity):
    """Publish one field from a common coordinator snapshot."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, key: str,
                 name: str, icon: str) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_icon = icon

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.key)
        if self.key == "days_until_trip":
            return value
        if self.key == "upcoming_trips":
            return self.coordinator.data.get("upcoming_count", 0)
        if not value:
            return None
        if self.key == "next_trip":
            return value["destination"]
        return value["description"]

    @property
    def extra_state_attributes(self) -> dict:
        value = self.coordinator.data.get(self.key)
        if self.key == "upcoming_trips":
            return {"trips": value or []}
        if isinstance(value, dict):
            return value
        return {}
