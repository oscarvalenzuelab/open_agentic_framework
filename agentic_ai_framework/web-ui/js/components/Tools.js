// js/components/Tools.js - Tools Component

const Tools = () => {
    const { useState, useEffect } = React;

    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState(null);
    const [configuringTool, setConfiguringTool] = useState(null);
    const [toolConfig, setToolConfig] = useState('');
    const [savingConfig, setSavingConfig] = useState(false);

    useEffect(() => {
        loadTools();
    }, []);

    const loadTools = async () => {
        try {
            setLoading(true);
            const toolsData = await api.getTools();
            setTools(Array.isArray(toolsData) ? toolsData : []);
        } catch (error) {
            console.error('Failed to load tools:', error);
            setTools([]);
        } finally {
            setLoading(false);
        }
    };

    const handleExecuteTool = async (tool) => {
        const parametersStr = prompt(
            `Enter parameters for ${tool.name} (JSON format):\n\nExample: ${JSON.stringify(getExampleParameters(tool), null, 2)}`
        );
        
        if (!parametersStr) return;

        try {
            const parameters = JSON.parse(parametersStr);
            setExecuting(tool.name);
            const result = await api.executeTool(tool.name, parameters);
            alert(`Tool executed successfully!\n\nResult: ${JSON.stringify(result, null, 2)}`);
        } catch (error) {
            if (error instanceof SyntaxError) {
                alert('Invalid JSON format in parameters');
            } else {
                alert('Failed to execute tool: ' + error.message);
            }
        } finally {
            setExecuting(null);
        }
    };

    const handleConfigureTool = async (tool) => {
        setConfiguringTool(tool);
        setSavingConfig(false);
        setToolConfig('');
        try {
            const config = await api.getToolConfig(tool.name);
            setToolConfig(JSON.stringify(config, null, 2));
        } catch (err) {
            setToolConfig('{}');
        }
    };

    const handleSaveConfig = async () => {
        if (!configuringTool) return;
        setSavingConfig(true);
        try {
            const configObj = JSON.parse(toolConfig);
            await api.configureTool(configuringTool.name, configObj);
            alert('Configuration saved!');
            setConfiguringTool(null);
            setToolConfig('');
        } catch (err) {
            alert('Failed to save config: ' + err.message);
        } finally {
            setSavingConfig(false);
        }
    };

    const getExampleParameters = (tool) => {
        switch (tool.name) {
            case 'website_monitor':
                return { url: 'https://google.com', expected_status: 200, timeout: 10 };
            case 'email_sender':
                return { to: 'user@example.com', subject: 'Test', body: 'Hello World' };
            case 'http_client':
                return { url: 'https://api.example.com', method: 'GET' };
            case 'file_reader':
                return { path: '/path/to/file.txt' };
            case 'database_query':
                return { query: 'SELECT * FROM users LIMIT 5' };
            default:
                return {};
        }
    };

    if (loading) return React.createElement(Loading, { message: "Loading tools..." });

    return React.createElement('div', {}, [
        React.createElement('div', { 
            key: 'main-card',
            className: 'card' 
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'card-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'card-title' 
                }, 'Available Tools'),
                React.createElement('button', {
                    key: 'refresh',
                    className: 'btn btn-secondary',
                    onClick: loadTools,
                    title: 'Refresh'
                }, React.createElement('i', { className: 'fas fa-refresh' }))
            ]),
            React.createElement('div', { 
                key: 'content',
                className: 'card-content' 
            }, 
                tools.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-tools'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No tools available'),
                        React.createElement('p', { key: 'description' }, 'Tools will appear here when they are configured in your backend.')
                    ]) :
                    React.createElement('div', {
                        key: 'tools-grid',
                        className: 'grid grid-2'
                    }, tools
                        .sort((a, b) => a.name.localeCompare(b.name))
                        .map(tool => 
                        React.createElement('div', {
                            key: tool.id || tool.name,
                            className: 'card tool-card'
                        }, [
                            React.createElement('div', { 
                                key: 'header',
                                className: 'card-header' 
                            }, [
                                React.createElement('h4', { 
                                    key: 'title',
                                    className: 'card-title' 
                                }, tool.name),
                                React.createElement('span', {
                                    key: 'status',
                                    className: `status ${tool.enabled ? 'status-online' : 'status-offline'}`
                                }, tool.enabled ? 'Enabled' : 'Disabled')
                            ]),
                            React.createElement('div', { 
                                key: 'content',
                                className: 'card-content' 
                            }, [
                                React.createElement('p', {
                                    key: 'description',
                                    style: { marginBottom: '16px', color: '#64748b' }
                                }, tool.description || 'No description available'),
                                tool.parameters_schema && React.createElement('div', {
                                    key: 'parameters',
                                    className: 'tool-parameters'
                                }, [
                                    React.createElement('strong', { key: 'title' }, 'Parameters:'),
                                    React.createElement('pre', {
                                        key: 'schema'
                                    }, JSON.stringify(tool.parameters_schema, null, 2))
                                ]),
                                React.createElement('div', { key: 'actions', style: { marginTop: '12px', display: 'flex', gap: '8px' } }, [
                                    React.createElement('button', {
                                        key: 'execute',
                                        className: 'btn btn-primary',
                                        disabled: executing === tool.name,
                                        onClick: () => handleExecuteTool(tool)
                                    }, executing === tool.name ? 'Running...' : 'Execute'),
                                    React.createElement('button', {
                                        key: 'configure',
                                        className: 'btn btn-secondary',
                                        onClick: () => handleConfigureTool(tool)
                                    }, 'Configure')
                                ])
                            ])
                        ])
                    ))
            )
        ]),
        configuringTool && React.createElement('div', {
            key: 'config-modal',
            className: 'modal-overlay',
            onClick: () => setConfiguringTool(null)
        }, React.createElement('div', {
            className: 'modal',
            onClick: e => e.stopPropagation()
        }, [
            React.createElement('div', { className: 'modal-header', key: 'header' }, [
                React.createElement('h3', { className: 'modal-title', key: 'title' }, `Configure Tool: ${configuringTool.name}`),
                React.createElement('button', {
                    className: 'modal-close',
                    onClick: () => setConfiguringTool(null),
                    key: 'close'
                }, React.createElement('i', { className: 'fas fa-times' }))
            ]),
            React.createElement('div', { className: 'modal-content', key: 'content' }, [
                React.createElement('p', { style: { color: '#64748b', marginBottom: '8px' }, key: 'desc' }, configuringTool.description),
                React.createElement('textarea', {
                    key: 'config-textarea',
                    className: 'form-textarea',
                    value: toolConfig,
                    onChange: e => setToolConfig(e.target.value),
                    style: { minHeight: '120px', fontFamily: 'monospace', fontSize: '13px', width: '100%' },
                    placeholder: 'Enter tool configuration as JSON (e.g. credentials, API keys, etc.)'
                }),
                React.createElement('div', { style: { marginTop: '12px', display: 'flex', gap: '8px' }, key: 'actions' }, [
                    React.createElement('button', {
                        className: 'btn btn-primary',
                        onClick: handleSaveConfig,
                        disabled: savingConfig
                    }, savingConfig ? 'Saving...' : 'Save'),
                    React.createElement('button', {
                        className: 'btn btn-secondary',
                        onClick: () => setConfiguringTool(null)
                    }, 'Cancel')
                ])
            ])
        ]))
    ]);
};

// Make component globally available
window.Tools = Tools;