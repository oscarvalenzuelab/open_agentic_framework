// js/App.js - Main App Component

const App = () => {
    const { useState } = React;

    const [currentPage, setCurrentPage] = useState('dashboard');
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const pages = {
        dashboard: { 
            title: 'Dashboard', 
            component: Dashboard || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-exclamation-triangle' }),
                React.createElement('h3', { key: 'title' }, 'Dashboard not available'),
                React.createElement('p', { key: 'desc' }, 'The Dashboard component failed to load.')
            ])),
            icon: 'fas fa-chart-line'
        },
        agents: { 
            title: 'AI Agents', 
            component: AgentManagement || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-exclamation-triangle' }),
                React.createElement('h3', { key: 'title' }, 'Agent Management not available'),
                React.createElement('p', { key: 'desc' }, 'The AgentManagement component failed to load.')
            ])),
            icon: 'fas fa-robot'
        },
        workflows: { 
            title: 'Workflows', 
            component: WorkflowBuilder || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-project-diagram' }),
                React.createElement('h3', { key: 'title' }, 'Workflows - Coming Soon'),
                React.createElement('p', { key: 'desc' }, 'Workflow builder will be available in a future update.')
            ])),
            icon: 'fas fa-project-diagram'
        },
        scheduling: { 
            title: 'Scheduling', 
            component: Scheduling || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-calendar-alt' }),
                React.createElement('h3', { key: 'title' }, 'Scheduling - Coming Soon'),
                React.createElement('p', { key: 'desc' }, 'Task scheduling will be available in a future update.')
            ])),
            icon: 'fas fa-calendar-alt'
        },
        providers: { 
            title: 'Providers & Models', 
            component: ProviderManagement || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-server' }),
                React.createElement('h3', { key: 'title' }, 'Provider Management - Coming Soon'),
                React.createElement('p', { key: 'desc' }, 'Provider and model management will be available in a future update.')
            ])),
            icon: 'fas fa-server'
        },
        tools: { 
            title: 'Tools', 
            component: Tools || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-tools' }),
                React.createElement('h3', { key: 'title' }, 'Tools - Coming Soon'),
                React.createElement('p', { key: 'desc' }, 'Tools management will be available in a future update.')
            ])),
            icon: 'fas fa-tools'
        },
        backup: { 
            title: 'Backup & Restore', 
            component: BackupManagement || (() => React.createElement('div', { className: 'empty-state' }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-archive' }),
                React.createElement('h3', { key: 'title' }, 'Backup Management - Coming Soon'),
                React.createElement('p', { key: 'desc' }, 'Backup and restore functionality will be available in a future update.')
            ])),
            icon: 'fas fa-archive'
        }
    };

    const CurrentComponent = pages[currentPage].component;

    const handleNavClick = (page) => {
        setCurrentPage(page);
        setSidebarOpen(false); // Close sidebar on mobile after navigation
    };

    const toggleSidebar = () => {
        setSidebarOpen(!sidebarOpen);
    };

    return React.createElement('div', { className: 'app' }, [
        // Sidebar Overlay (Mobile)
        React.createElement('div', {
            key: 'overlay',
            className: `sidebar-overlay ${sidebarOpen ? 'open' : ''}`,
            onClick: () => setSidebarOpen(false)
        }),

        // Sidebar
        React.createElement('div', { 
            key: 'sidebar',
            className: `sidebar ${sidebarOpen ? 'open' : ''}` 
        }, [
            // Sidebar Header
            React.createElement('div', { 
                key: 'header',
                className: 'sidebar-header' 
            }, 
                React.createElement('div', { className: 'logo' }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: 'fas fa-brain' 
                    }),
                    'Open Agentic'
                ])
            ),
            
            // Navigation Menu
            React.createElement('nav', { 
                key: 'nav',
                className: 'nav-menu' 
            }, Object.entries(pages).map(([pageKey, page]) =>
                React.createElement('button', {
                    key: pageKey,
                    className: `nav-item ${currentPage === pageKey ? 'active' : ''}`,
                    onClick: () => handleNavClick(pageKey)
                }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: page.icon 
                    }),
                    page.title
                ])
            ))
        ]),

        // Main Content
        React.createElement('div', { 
            key: 'main',
            className: 'main-content' 
        }, [
            // Header
            React.createElement('header', { 
                key: 'header',
                className: 'header' 
            }, [
                React.createElement('div', { 
                    key: 'left',
                    className: 'header-left' 
                }, [
                    React.createElement('button', {
                        key: 'menu-btn',
                        className: 'mobile-menu-btn',
                        onClick: toggleSidebar
                    }, React.createElement('i', { className: 'fas fa-bars' })),
                    React.createElement('h1', { 
                        key: 'title',
                        className: 'page-title' 
                    }, pages[currentPage].title)
                ]),
                
                React.createElement('div', { 
                    key: 'actions',
                    className: 'header-actions' 
                }, [
                    React.createElement('a', {
                        key: 'docs',
                        href: '/docs',
                        target: '_blank',
                        className: 'btn btn-secondary',
                        title: 'Open API Documentation'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-book'
                        }),
                        ' API Docs'
                    ]),
                    React.createElement('button', {
                        key: 'health',
                        className: 'btn btn-secondary',
                        onClick: () => window.open('/health', '_blank'),
                        title: 'Check System Health'
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-heartbeat' 
                        }),
                        ' Health'
                    ])
                ])
            ]),

            // Content Area
            React.createElement('main', { 
                key: 'content',
                className: 'content' 
            }, React.createElement(CurrentComponent))
        ])
    ]);
};

// Make component globally available
window.App = App;