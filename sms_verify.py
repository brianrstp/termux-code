"""
Gmail Creator - SMS Verification Module
Supports SMS-Activate, 5sim.net, and manual verification.
Works on Termux without modification.
"""
import asyncio
import time
import requests
from abc import ABC, abstractmethod

from config import (
    SMS_PROVIDER, SMS_ACTIVATE_API_KEY, FIVE_SIM_API_KEY,
)


class SmsProvider(ABC):
    """Abstract base class for SMS verification providers."""

    @abstractmethod
    async def get_number(self, service: str = "go") -> dict:
        """Get a phone number. Returns {"id": ..., "number": ...}."""
        pass

    @abstractmethod
    async def get_code(self, sms_id: str, timeout: int = 120) -> str:
        """Wait for and return SMS code."""
        pass

    @abstractmethod
    async def cancel_number(self, sms_id: str):
        """Cancel/release the phone number."""
        pass


class SmsActivateProvider(SmsProvider):
    """SMS-Activate.org provider."""

    BASE_URL = "https://api.sms-activate.org/stubs/handler_api.php"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _request(self, params: dict) -> str:
        params["api_key"] = self.api_key
        resp = requests.get(self.BASE_URL, params=params, timeout=30)
        return resp.text

    async def get_number(self, service: str = "go") -> dict:
        result = await self._request({
            "action": "getNumber",
            "service": service,
            "country": 0,  # Any country
        })
        if result.startswith("ACCESS_NUMBER"):
            parts = result.split(":")
            return {"id": parts[1], "number": parts[2]}
        raise Exception(f"SMS-Activate error: {result}")

    async def get_code(self, sms_id: str, timeout: int = 120) -> str:
        start = time.time()
        while time.time() - start < timeout:
            result = await self._request({
                "action": "getStatus",
                "id": sms_id,
            })
            if result.startswith("STATUS_OK"):
                code = result.split(":")[1]
                return code
            await asyncio.sleep(5)
        raise TimeoutError("SMS code not received within timeout")

    async def cancel_number(self, sms_id: str):
        await self._request({"action": "setStatus", "id": sms_id, "status": "8"})


class FiveSimProvider(SmsProvider):
    """5sim.net provider."""

    BASE_URL = "https://5sim.net/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def get_number(self, service: str = "google") -> dict:
        resp = requests.post(
            f"{self.BASE_URL}/purchase",
            headers=self.headers,
            json={
                "product": "activation",
                "category": "any",
                "operator": "any",
                "country": "any",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"id": str(data["id"]), "number": str(data["phone"])}
        raise Exception(f"5sim error: {resp.text}")

    async def get_code(self, sms_id: str, timeout: int = 120) -> str:
        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(
                f"{self.BASE_URL}/check/{sms_id}",
                headers=self.headers,
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("sms"):
                    return data["sms"][0]["code"]
            await asyncio.sleep(5)
        raise TimeoutError("SMS code not received within timeout")

    async def cancel_number(self, sms_id: str):
        requests.get(
            f"{self.BASE_URL}/cancel/{sms_id}",
            headers=self.headers,
            timeout=30,
        )


class ManualSmsProvider(SmsProvider):
    """Manual SMS verification - user enters code manually."""

    async def get_number(self, service: str = "go") -> dict:
        print("\n📱 Manual SMS Verification")
        print("Enter your phone number for verification:")
        number = input("Phone number: ").strip()
        return {"id": "manual", "number": number}

    async def get_code(self, sms_id: str, timeout: int = 300) -> str:
        print("\nEnter the verification code you received:")
        code = input("Code: ").strip()
        return code

    async def cancel_number(self, sms_id: str):
        pass


class SmsVerifier:
    """Unified SMS verification interface."""

    def __init__(self, provider_name: str = None):
        provider_name = provider_name or SMS_PROVIDER
        if provider_name == "sms_activate":
            self.provider = SmsActivateProvider(SMS_ACTIVATE_API_KEY)
        elif provider_name == "five_sim":
            self.provider = FiveSimProvider(FIVE_SIM_API_KEY)
        else:
            self.provider = ManualSmsProvider()

    async def get_number(self, service: str = "go") -> dict:
        return await self.provider.get_number(service)

    async def get_code(self, sms_id: str, timeout: int = 120) -> str:
        return await self.provider.get_code(sms_id, timeout)

    async def cancel_number(self, sms_id: str):
        return await self.provider.cancel_number(sms_id)
