import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import TeamSettings from '@/components/settings/TeamSettings'
import CannedResponses from '@/components/settings/CannedResponses'
import SLASettings from '@/components/settings/SLASettings'
import WebhookSettings from '@/components/settings/WebhookSettings'
import DomainSettings from '@/components/settings/DomainSettings'
import APIKeySettings from '@/components/settings/APIKeySettings'
import InboxSettings from '@/components/settings/InboxSettings'

const TABS = [
  { key: 'team', label: 'Team' },
  { key: 'inboxes', label: 'Inboxes' },
  { key: 'canned', label: 'Canned Responses' },
  { key: 'sla', label: 'SLA' },
  { key: 'webhooks', label: 'Webhooks' },
  { key: 'apikeys', label: 'API Keys' },
  { key: 'domains', label: 'Custom Domains' },
]

export default function SettingsPage() {
  const { tab } = useParams<{ tab?: string }>()
  const navigate = useNavigate()
  const activeTab = tab || 'team'

  return (
    <div className="h-full flex bg-white">
      {/* Sidebar */}
      <div className="w-52 border-r border-gray-200 py-4 shrink-0">
        <div className="px-4 mb-4">
          <h2 className="font-semibold text-gray-900">Settings</h2>
        </div>
        <nav className="space-y-0.5">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => navigate(`/settings/${t.key}`)}
              className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                activeTab === t.key
                  ? 'bg-indigo-50 text-indigo-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'team' && <TeamSettings />}
        {activeTab === 'inboxes' && <InboxSettings />}
        {activeTab === 'canned' && <CannedResponses />}
        {activeTab === 'sla' && <SLASettings />}
        {activeTab === 'webhooks' && <WebhookSettings />}
        {activeTab === 'apikeys' && <APIKeySettings />}
        {activeTab === 'domains' && <DomainSettings />}
      </div>
    </div>
  )
}
