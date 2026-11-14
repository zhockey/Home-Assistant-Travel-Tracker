"""Travel day and upcoming travel indicators."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([
        TravelBinarySensor(coordinator, entry.entry_id, "travel_today", "Travel Today"),
        TravelBinarySensor(
            coordinator, entry.entry_id, "travel_this_week", "Travel Next 7 Days"
        ),
    ])


class TravelBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Represent trip activity in the local calendar window."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bag-checked"

    def __init__(self, coordinator, entry_id: str,
                 key: str, name: str) -> None:
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get(self.key))
