from harness.tools import (
    BlenderExecutePythonTool,
    BlenderRenderTool,
    BrowserClickTool,
    BrowserFillTool,
    BrowserNavigateTool,
    FilesystemReadTool,
    FilesystemWriteTool,
    ShellRunTool,
    ToolRisk,
    UnityExecuteEditorScriptTool,
    UnityProjectInfoTool,
)


def test_arbitrary_execution_and_side_effect_tools_remain_dangerous() -> None:
    assert ShellRunTool.risk is ToolRisk.DANGEROUS
    assert BrowserClickTool.risk is ToolRisk.DANGEROUS
    assert BlenderExecutePythonTool.risk is ToolRisk.DANGEROUS
    assert UnityExecuteEditorScriptTool.risk is ToolRisk.DANGEROUS


def test_known_read_and_write_tools_keep_expected_risk_boundaries() -> None:
    assert FilesystemReadTool.risk is ToolRisk.READ
    assert FilesystemWriteTool.risk is ToolRisk.WRITE
    assert BrowserNavigateTool.risk is ToolRisk.READ
    assert BrowserFillTool.risk is ToolRisk.WRITE
    assert BlenderRenderTool.risk is ToolRisk.WRITE
    assert UnityProjectInfoTool.risk is ToolRisk.READ
