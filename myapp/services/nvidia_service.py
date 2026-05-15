import os
import logging
import requests
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NVIDIAServiceError(Exception):
    """Excepción específica para errores del servicio NVIDIA."""


class NVIDIABuildService:
    """Servicio para interactuar con NVIDIA Build API"""

    DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"
    DEFAULT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(self):
        self.api_key = getattr(settings, 'NVIDIA_API_KEY', None) or os.getenv('NVIDIA_API_KEY')
        self.base_url = getattr(settings, 'NVIDIA_API_URL', self.DEFAULT_URL)
        self.model = getattr(settings, 'NVIDIA_API_MODEL', self.DEFAULT_MODEL)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers para la API de NVIDIA"""
        if not self.api_key:
            raise NVIDIAServiceError(
                "NVIDIA_API_KEY no está configurada. Definéla en el archivo .env."
            )

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _call_chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """Realiza la llamada al endpoint de chat y devuelve el contenido o None."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )
        except requests.exceptions.Timeout:
            logger.warning("Timeout al conectar con NVIDIA Build API")
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Error de conexión con NVIDIA Build API: %s", exc)
            return None
        except NVIDIAServiceError as exc:
            logger.error("%s", exc)
            return None

        if response.status_code != 200:
            logger.error(
                "Error en API NVIDIA: %s - %s", response.status_code, response.text[:300]
            )
            return None

        try:
            data = response.json()
            return data['choices'][0]['message']['content']
        except (ValueError, KeyError, IndexError) as exc:
            logger.error("Respuesta inesperada de NVIDIA Build API: %s", exc)
            return None
    
    def _build_team_prompt(self, creature_data: List[Dict]) -> str:
        """Construye el prompt con información del equipo"""
        prompt = "Eres un experto en estrategia de combate estilo Pokémon. "
        prompt += "Analiza el siguiente equipo de criaturas y da recomendaciones estratégicas:\n\n"
        
        for i, creature in enumerate(creature_data, 1):
            prompt += f"Criatura {i}: {creature['name']}\n"
            prompt += f"  - Tipo: {creature['type']}\n"
            prompt += f"  - HP: {creature['hp']}, ATK: {creature['attack']}, DEF: {creature['defense']}\n"
            prompt += f"  - SPD: {creature['speed']}, SP.ATK: {creature['sp_attack']}, SP.DEF: {creature['sp_defense']}\n"
            prompt += f"  - Movimientos: {', '.join(creature['moves'])}\n\n"
        
        prompt += "\nProporciona 3-5 recomendaciones estratégicas específicas para este equipo. "
        prompt += "Incluye sugerencias sobre sinergia entre tipos, movimientos recomendados, "
        prompt += "y estrategias de combate. Sé conciso y práctico."
        
        return prompt
    
    def get_team_recommendations(self, creature_data: List[Dict]) -> Optional[str]:
        """Obtiene recomendaciones estratégicas para un equipo de criaturas."""
        if not creature_data:
            logger.warning("get_team_recommendations llamado sin criaturas")
            return None
        prompt = self._build_team_prompt(creature_data)
        return self._call_chat(prompt, max_tokens=500)
    
    def get_battle_recommendation(self, player_creature: Dict, enemy_creature: Dict) -> Optional[str]:
        """
        Obtiene recomendación para un combate específico
        
        Args:
            player_creature: Diccionario con información de la criatura del jugador
            enemy_creature: Diccionario con información de la criatura enemiga
        
        Returns:
            String con recomendación o None si hay error
        """
        prompt = (
            "Eres un experto en combate estilo Pokémon. "
            "Analiza este enfrentamiento y da una recomendación estratégica:\n\n"
            f"Tu criatura: {player_creature['name']}\n"
            f"  - Tipo: {player_creature['type']}\n"
            f"  - HP: {player_creature['hp']}, ATK: {player_creature['attack']}, DEF: {player_creature['defense']}\n"
            f"  - SPD: {player_creature['speed']}\n"
            f"  - Movimientos: {', '.join(player_creature['moves'])}\n\n"
            f"Criatura enemiga: {enemy_creature['name']}\n"
            f"  - Tipo: {enemy_creature['type']}\n"
            f"  - HP: {enemy_creature['hp']}, ATK: {enemy_creature['attack']}, DEF: {enemy_creature['defense']}\n"
            f"  - SPD: {enemy_creature['speed']}\n\n"
            "Recomienda qué movimiento usar y por qué. Considera ventajas de tipo y estadísticas."
        )
        return self._call_chat(prompt, max_tokens=300)
