"""Repositorios concretos sobre JSON, cumplen los Protocols de core/."""

from persistence.repositorios.repo_anulaciones import RepositorioAnulacionesJSON
from persistence.repositorios.repo_clientes import RepositorioAbonosJSON, RepositorioClientesJSON
from persistence.repositorios.repo_gastos import RepositorioGastosJSON
from persistence.repositorios.repo_movimientos import RepositorioMovimientosJSON
from persistence.repositorios.repo_productos import RepositorioProductosJSON
from persistence.repositorios.repo_tasa import RepositorioTasaJSON
from persistence.repositorios.repo_ventas import RepositorioVentasJSON

__all__ = [
    "RepositorioAnulacionesJSON",
    "RepositorioAbonosJSON",
    "RepositorioClientesJSON",
    "RepositorioGastosJSON",
    "RepositorioMovimientosJSON",
    "RepositorioProductosJSON",
    "RepositorioTasaJSON",
    "RepositorioVentasJSON",
]
