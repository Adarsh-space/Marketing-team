"""
Zoho Analytics Service

Handles data visualization and reporting:
- Create workspaces and tables
- Import data for visualization
- Generate charts (75+ types)
- Export reports
- Dashboard management
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class ZohoAnalyticsService:
    """
    Complete Zoho Analytics integration for data visualization and reporting.
    """

    # Zoho Analytics API base URL
    API_BASE_URL = "https://analyticsapi.zoho.com/restapi/v2"

    def __init__(self, auth_service):
        """
        Initialize Zoho Analytics Service.

        Args:
            auth_service: ZohoAuthService instance for authentication
        """
        self.auth_service = auth_service
        logger.info("Zoho Analytics Service initialized")

    async def _get_headers(self, user_id: str = "default_user") -> Optional[Dict[str, str]]:
        """Get authorization headers with valid access token."""
        access_token = await self.auth_service.get_valid_access_token(user_id)
        if not access_token:
            logger.error(f"No valid access token for user: {user_id}")
            return None

        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }

    async def create_workspace(
        self,
        workspace_name: str,
        description: str = "",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a new workspace (database) in Zoho Analytics.

        Args:
            workspace_name: Name of the workspace
            description: Description
            user_id: User identifier

        Returns:
            Dict with workspace details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {
                    "status": "error",
                    "message": "No valid Zoho connection"
                }

            url = f"{self.API_BASE_URL}/workspaces"
            workspace_data = {
                "workspaceName": workspace_name,
                "description": description
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=workspace_data)

                if response.status_code in [200, 201]:
                    result = response.json()
                    workspace_id = result.get("data", {}).get("workspaceId")

                    logger.info(f"Created workspace: {workspace_name} ({workspace_id})")

                    return {
                        "status": "success",
                        "workspace_id": workspace_id,
                        "workspace_name": workspace_name,
                        "message": "Workspace created successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create workspace")
                    }

        except Exception as e:
            logger.error(f"Error creating workspace: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def create_table(
        self,
        workspace_id: str,
        table_name: str,
        columns: List[Dict[str, Any]],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a table in workspace.

        Args:
            workspace_id: Workspace ID
            table_name: Table name
            columns: List of column definitions [{"columnName": "Name", "dataType": "PLAIN"}]
            user_id: User identifier

        Returns:
            Dict with table creation status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/tables"
            table_data = {
                "tableName": table_name,
                "tableDesign": {
                    "columns": columns
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=table_data)

                if response.status_code in [200, 201]:
                    logger.info(f"Created table: {table_name} in workspace {workspace_id}")

                    return {
                        "status": "success",
                        "table_name": table_name,
                        "message": "Table created successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create table")
                    }

        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def import_data(
        self,
        workspace_id: str,
        table_name: str,
        data: List[Dict[str, Any]],
        import_type: str = "append",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Import data into a table.

        Args:
            workspace_id: Workspace ID
            table_name: Table name
            data: List of data rows
            import_type: "append", "truncateadd", or "updateadd"
            user_id: User identifier

        Returns:
            Dict with import status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/data"
            import_data_payload = {
                "tableName": table_name,
                "data": data,
                "importType": import_type
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=import_data_payload)

                if response.status_code in [200, 201]:
                    logger.info(f"Imported {len(data)} rows into {table_name}")

                    return {
                        "status": "success",
                        "rows_imported": len(data),
                        "message": "Data imported successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to import data")
                    }

        except Exception as e:
            logger.error(f"Error importing data: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def create_chart(
        self,
        workspace_id: str,
        view_name: str,
        chart_config: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a chart/visualization.

        Args:
            workspace_id: Workspace ID
            view_name: Name for the chart
            chart_config: Chart configuration
                {
                    "chartType": "bar|line|pie|scatter|funnel|...",
                    "tableName": "...",
                    "xAxis": "...",
                    "yAxis": "...",
                    "aggregation": "sum|avg|count|...",
                    ...
                }
            user_id: User identifier

        Returns:
            Dict with chart details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/views"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json={
                    "viewName": view_name,
                    **chart_config
                })

                if response.status_code in [200, 201]:
                    result = response.json()
                    view_id = result.get("data", {}).get("viewId")

                    logger.info(f"Created chart: {view_name} ({view_id})")

                    return {
                        "status": "success",
                        "view_id": view_id,
                        "view_name": view_name,
                        "message": "Chart created successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create chart")
                    }

        except Exception as e:
            logger.error(f"Error creating chart: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_chart_data(
        self,
        workspace_id: str,
        view_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get data from a chart/view.

        Args:
            workspace_id: Workspace ID
            view_id: View/Chart ID
            user_id: User identifier

        Returns:
            Dict with chart data
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/views/{view_id}/data"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "data": result.get("data", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get chart data"
                    }

        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def export_data(
        self,
        workspace_id: str,
        table_or_view_name: str,
        export_format: str = "json",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Export data from table or view.

        Args:
            workspace_id: Workspace ID
            table_or_view_name: Table or view name
            export_format: "json", "csv", "html", "pdf", "image"
            user_id: User identifier

        Returns:
            Dict with exported data or download URL
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/views/{table_or_view_name}/data"
            params = {"responseFormat": export_format}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    if export_format == "json":
                        result = response.json()
                        return {
                            "status": "success",
                            "data": result
                        }
                    else:
                        # For other formats, return content
                        return {
                            "status": "success",
                            "content": response.content,
                            "format": export_format
                        }
                else:
                    return {
                        "status": "error",
                        "message": "Export failed"
                    }

        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def run_sql_query(
        self,
        workspace_id: str,
        sql_query: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Run SQL query on workspace.

        Args:
            workspace_id: Workspace ID
            sql_query: SQL query
            user_id: User identifier

        Returns:
            Dict with query results
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/sqlquery"
            query_data = {"sqlQuery": sql_query}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=query_data)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "data": result.get("data", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Query failed"
                    }

        except Exception as e:
            logger.error(f"Error running SQL query: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def list_workspaces(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        List all workspaces.

        Args:
            user_id: User identifier

        Returns:
            Dict with workspaces list
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "workspaces": result.get("data", {}).get("workspaces", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to list workspaces"
                    }

        except Exception as e:
            logger.error(f"Error listing workspaces: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_workspace_metadata(
        self,
        workspace_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get workspace metadata (tables, views, etc.).

        Args:
            workspace_id: Workspace ID
            user_id: User identifier

        Returns:
            Dict with workspace metadata
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/metadata"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "metadata": result.get("data", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get metadata"
                    }

        except Exception as e:
            logger.error(f"Error getting workspace metadata: {str(e)}")
            return {"status": "error", "message": str(e)}
