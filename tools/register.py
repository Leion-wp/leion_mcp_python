from tools.fs_tools import register_fs_tools
from tools.fs_patch import register_fs_patch_tools
from tools.workflow_tools import register_workflow_tools
from tools.git_tools import register_git_tools
from tools.project_tools import register_project_tools
from tools.flowise_tools import register_flowise_rube_zapier_tools
from tools.vector_memory_tools import register_vector_memory_tools
from tools.workflow_builder_tools import register_workflow_builder_tools
from tools.agent_tools import register_agent_tools
from tools.fs_watch_tools import register_fs_watch_tools
from tools.composio_tools import register_composio_tools
from tools.llm_router_tools import register_llm_router_tools
from tools.business_launcher_tools import register_business_launcher_tools
from tools.business_assets_tools import register_business_assets_tools
from tools.repo_builder_tools import register_repo_builder_tools
from tools.code_refactorer_tools import register_code_refactorer_tools
from tools.dependency_ai_tools import register_dependency_ai_tools
from tools.observability_tools import register_observability_tools
from tools.composio_business_tools import register_composio_business_tools
from tools.auto_tester_tools import register_auto_tester_tools
from tools.fs_monitor_pro_tools import register_fs_monitor_pro_tools
from tools.profile_ai_tools import register_profile_ai_tools
from tools.agent_supervisor_tools import register_agent_supervisor_tools
from tools.comm_tools import register_comm_tools
from tools.ui_component_generator_tools import register_ui_component_generator_tools
from tools.asset_creator_tools import register_asset_creator_tools
from tools.memory_tools import register_memory_tools
from tools.leion_cc_dashboard_tools import register_leion_cc_dashboard_tools
from tools.leion_cc_workflows_tools import register_leion_cc_workflows_tools
from tools.leion_cc_run_workflow_tools import register_leion_cc_run_workflow_tools
from tools.leion_cc_agents_tools import register_leion_cc_agents_tools
from tools.composio_list_apps_tools import register_composio_list_apps_tools
from tools.composio_connect_app_tools import register_composio_connect_app_tools
from tools.leion_cc_resources import register_leion_cc_resources
from tools.leion_ai_intelligence_tools import register_leion_ai_intelligence_tools
from tools.leion_ai_workflow_engine_tools import register_leion_ai_workflow_engine_tools
from tools.orchestrator_tools import register_orchestrator_tools
from tools.system_automation_tools import register_system_automation_tools

# from tools.shell_tools import register_shell_tools


def register_all_tools(server):
    register_fs_tools(server)
    register_workflow_tools(server)
    register_git_tools(server)
    register_project_tools(server)
    register_flowise_rube_zapier_tools(server)
    register_vector_memory_tools(server)
    register_workflow_builder_tools(server)
    register_agent_tools(server)
    register_fs_watch_tools(server)
    register_composio_tools(server)
    register_llm_router_tools(server)
    register_business_launcher_tools(server)
    register_business_assets_tools(server)
    register_repo_builder_tools(server)
    register_code_refactorer_tools(server)
    register_dependency_ai_tools(server)
    register_observability_tools(server)
    register_composio_business_tools(server)
    register_auto_tester_tools(server)
    register_fs_monitor_pro_tools(server)
    register_profile_ai_tools(server)
    register_agent_supervisor_tools(server)
    register_comm_tools(server)
    register_ui_component_generator_tools(server)
    register_asset_creator_tools(server)
    register_memory_tools(server)
    register_leion_cc_dashboard_tools(server)
    register_leion_cc_workflows_tools(server)
    register_leion_cc_run_workflow_tools(server)
    register_leion_cc_agents_tools(server)
    register_composio_list_apps_tools(server)
    register_composio_connect_app_tools(server)
    register_leion_cc_resources(server)
    register_leion_ai_intelligence_tools(server)
    register_leion_ai_workflow_engine_tools(server)
    register_orchestrator_tools(server)
    register_system_automation_tools(server)
    register_fs_patch_tools(server)
    # register_shell_tools(server)
