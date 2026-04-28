<template>
  <DesktopLayout :is-sidebar-collapsed="isSidebarCollapsed" @close-sidebar="setSidebarCollapsed(true)">
    <template #sidebar>
      <section class="sidebar-root">
        <div class="sidebar-scrollable">
          <SidebarThreadControls
            v-if="!isSidebarCollapsed"
            class="sidebar-thread-controls-host"
            :is-sidebar-collapsed="isSidebarCollapsed"
            :show-new-thread-button="true"
            @toggle-sidebar="setSidebarCollapsed(!isSidebarCollapsed)"
            @start-new-thread="onStartNewThreadFromToolbar"
          >
            <button
              class="sidebar-search-toggle"
              type="button"
              :aria-pressed="isSidebarSearchVisible"
              aria-label="Search threads"
              title="Search threads"
              @click="toggleSidebarSearch"
            >
              <IconTablerSearch class="sidebar-search-toggle-icon" />
            </button>
          </SidebarThreadControls>

          <div v-if="!isSidebarCollapsed && isSidebarSearchVisible" class="sidebar-search-bar">
            <IconTablerSearch class="sidebar-search-bar-icon" />
            <input
              ref="sidebarSearchInputRef"
              v-model="sidebarSearchQuery"
              class="sidebar-search-input"
              type="text"
              placeholder="Filter threads..."
              @keydown="onSidebarSearchKeydown"
            />
            <button
              v-if="sidebarSearchQuery.length > 0"
              class="sidebar-search-clear"
              type="button"
              aria-label="Clear search"
              @click="clearSidebarSearch"
            >
              <IconTablerX class="sidebar-search-clear-icon" />
            </button>
          </div>

          <button
            v-if="!isSidebarCollapsed"
            class="sidebar-skills-link"
            :class="{ 'is-active': isSkillsRoute }"
            type="button"
            @click="router.push({ name: 'skills' }); isMobile && setSidebarCollapsed(true)"
          >
            Capabilities
          </button>

          <SidebarThreadTree :groups="projectGroups" :project-display-name-by-id="projectDisplayNameById"
            v-if="!isSidebarCollapsed"
            :selected-thread-id="selectedThreadId" :is-loading="isLoadingThreads"
            :search-query="sidebarSearchQuery"
            :search-matched-thread-ids="serverMatchedThreadIds"
            @select="onSelectThread"
            @archive="onArchiveThread" @start-new-thread="onStartNewThread" @rename-project="onRenameProject"
            @rename-thread="onRenameThread"
            @remove-project="onRemoveProject" @reorder-project="onReorderProject"
            @export-thread="onExportThread" />
        </div>

        <div v-if="!isSidebarCollapsed" class="sidebar-settings-area">
          <Transition name="settings-panel">
            <div v-if="isSettingsOpen" class="sidebar-settings-panel">
              <div class="sidebar-settings-account-section">
                <div class="sidebar-settings-account-header">
                  <div class="sidebar-settings-account-header-main">
                    <button
                      class="sidebar-settings-account-collapse"
                      type="button"
                      :aria-expanded="!isAccountsSectionCollapsed"
                      :title="isAccountsSectionCollapsed ? 'Expand accounts' : 'Collapse accounts'"
                      @click="toggleAccountsSectionCollapsed"
                    >
                      <span class="sidebar-settings-account-collapse-icon">{{ isAccountsSectionCollapsed ? '▸' : '▾' }}</span>
                    </button>
                    <span class="sidebar-settings-account-title">Accounts</span>
                    <span class="sidebar-settings-account-count">{{ accounts.length }}</span>
                  </div>
                  <button
                    class="sidebar-settings-account-refresh"
                    type="button"
                    :disabled="isRefreshingAccounts || isSwitchingAccounts"
                    @click="onRefreshAccounts"
                  >
                    {{ isRefreshingAccounts ? 'Reloading…' : 'Reload' }}
                  </button>
                </div>
                <template v-if="!isAccountsSectionCollapsed">
                  <p v-if="accountActionError" class="sidebar-settings-account-error">{{ accountActionError }}</p>
                  <p v-if="accounts.length === 0" class="sidebar-settings-account-empty">
                    Run `codex login`, then click reload.
                  </p>
                  <div v-else class="sidebar-settings-account-list">
                  <article
                    v-for="account in accounts"
                    :key="account.accountId"
                    class="sidebar-settings-account-item"
                    :class="{
                      'is-active': account.isActive,
                      'is-unavailable': isAccountUnavailable(account),
                      'is-confirming-remove': isRemoveConfirmationActive(account),
                      'is-remove-visible': isRemoveVisible(account),
                    }"
                    :title="buildAccountTitle(account)"
                    @mouseenter="onAccountCardPointerEnter(account.accountId)"
                    @mouseleave="onAccountCardPointerLeave(account.accountId)"
                  >
                    <div class="sidebar-settings-account-main">
                      <p class="sidebar-settings-account-email">{{ account.email || 'Account' }}</p>
                      <p class="sidebar-settings-account-meta">
                        {{ formatAccountMeta(account) }}
                      </p>
                      <p class="sidebar-settings-account-quota">
                        {{ formatAccountQuota(account) }}
                      </p>
                      <p class="sidebar-settings-account-id">
                        Workspace {{ shortAccountId(account.accountId) }}
                      </p>
                    </div>
                    <div class="sidebar-settings-account-actions">
                      <button
                        class="sidebar-settings-account-switch"
                        type="button"
                        :disabled="isAccountActionDisabled(account) || account.isActive || isAccountUnavailable(account)"
                        @click="onSwitchAccount(account.accountId)"
                      >
                        {{ getAccountSwitchLabel(account) }}
                      </button>
                      <button
                        class="sidebar-settings-account-remove"
                        :class="{
                          'is-visible': isRemoveVisible(account),
                          'is-confirming': isRemoveConfirmationActive(account),
                        }"
                        type="button"
                        :disabled="isAccountActionDisabled(account)"
                        @click="onRemoveAccount(account.accountId)"
                      >
                        {{ getAccountRemoveLabel(account) }}
                      </button>
                    </div>
                  </article>
                  </div>
                </template>
              </div>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.sendWithEnter" @click="toggleSendWithEnter">
                <span class="sidebar-settings-label">Require ⌘ + enter to send</span>
                <span class="sidebar-settings-toggle" :class="{ 'is-on': !sendWithEnter }" />
              </button>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.inProgressSendMode" @click="cycleInProgressSendMode">
                <span class="sidebar-settings-label">When busy, new messages</span>
                <span class="sidebar-settings-value">{{ inProgressSendMode === 'steer' ? 'Redirect' : 'Hold' }}</span>
              </button>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.appearance" @click="cycleDarkMode">
                <span class="sidebar-settings-label">Appearance</span>
                <span class="sidebar-settings-value">{{ darkMode === 'system' ? 'System' : darkMode === 'dark' ? 'Dark' : 'Light' }}</span>
              </button>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.chatWidth" @click="cycleChatWidth">
                <span class="sidebar-settings-label">Chat width</span>
                <span class="sidebar-settings-value">{{ chatWidthLabel }}</span>
              </button>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.dictationClickToToggle" @click="toggleDictationClickToToggle">
                <span class="sidebar-settings-label">Click to toggle dictation</span>
                <span class="sidebar-settings-toggle" :class="{ 'is-on': dictationClickToToggle }" />
              </button>
              <button class="sidebar-settings-row" type="button" :title="SETTINGS_HELP.dictationAutoSend" @click="toggleDictationAutoSend">
                <span class="sidebar-settings-label">Auto send dictation</span>
                <span class="sidebar-settings-toggle" :class="{ 'is-on': dictationAutoSend }" />
              </button>

              <div class="sidebar-settings-row sidebar-settings-row--select" :title="SETTINGS_HELP.dictationLanguage">
                <span class="sidebar-settings-label">Dictation language</span>
                <ComposerDropdown
                  class="sidebar-settings-language-dropdown"
                  :model-value="dictationLanguage"
                  :options="dictationLanguageOptions"
                  placeholder="Auto-detect"
                  open-direction="up"
                  :enable-search="true"
                  search-placeholder="Search language..."
                  @update:model-value="onDictationLanguageChange"
                />
              </div>
              <button class="sidebar-settings-row" type="button" aria-live="polite" @click="onConnectTelegramBot">
                <span class="sidebar-settings-label">Telegram</span>
                <span class="sidebar-settings-value">{{ telegramStatusText }}</span>
              </button>
              <div
                v-if="showThreadContextBadge"
                class="sidebar-settings-row sidebar-settings-context-row"
                :data-state="threadContextBadgeState"
                :title="threadContextTooltip"
              >
                <span class="sidebar-settings-label">Context</span>
                <span class="sidebar-settings-context-value" :data-state="threadContextBadgeState">
                  {{ threadContextPrimaryText }}
                  <span class="sidebar-settings-context-meta">{{ threadContextSecondaryText }}</span>
                </span>
              </div>
              <div class="sidebar-settings-rate-limits">
                <RateLimitStatus :snapshots="accountRateLimitSnapshots" />
              </div>
              <div class="sidebar-settings-build-label" aria-label="Application version">
                OpenScience · v{{ appVersion }}
              </div>
            </div>
          </Transition>
          <button class="sidebar-settings-button" type="button" @click="isSettingsOpen = !isSettingsOpen">
            <IconTablerSettings class="sidebar-settings-icon" />
            <span>Settings</span>
            <span class="sidebar-settings-button-version">
              OpenScience · v{{ appVersion }}
            </span>
          </button>
        </div>
      </section>
    </template>

    <template #content>
      <section class="content-root" :style="contentStyle">
        <ContentHeader :title="contentTitle">
          <template #leading>
            <SidebarThreadControls
              v-if="isSidebarCollapsed || isMobile"
              class="sidebar-thread-controls-header-host"
              :is-sidebar-collapsed="isSidebarCollapsed"
              :show-new-thread-button="true"
              @toggle-sidebar="setSidebarCollapsed(!isSidebarCollapsed)"
              @start-new-thread="onStartNewThreadFromToolbar"
            />
          </template>
        </ContentHeader>

        <section class="content-body">
          <template v-if="isSkillsRoute">
            <SkillsHub @skills-changed="onSkillsChanged" />
          </template>
          <template v-else-if="isHomeRoute">
            <div class="content-grid content-grid-home">
              <div class="new-thread-empty">
                <p class="new-thread-hero">OpenScience</p>
                <p class="new-thread-subtitle">
                  Choose project context for the conversation, or review the current project notes and daily lab summary.
                </p>

                <section class="lab-home-panel" aria-label="Lab summaries and project context">
                  <div class="lab-panel-heading">
                    <div>
                      <p class="lab-panel-title">Lab context</p>
                      <p class="lab-panel-description">Project notes and daily summaries from the OpenScience workspace.</p>
                    </div>
                    <button
                      class="lab-panel-open"
                      type="button"
                      :disabled="!activeLabDocument"
                      @click="isLabReaderOpen = true"
                    >
                      Open reader
                    </button>
                  </div>
                  <div class="lab-home-controls">
                    <div class="lab-home-control-copy">
                      <label class="lab-project-select-label" for="lab-project-select">Conversation context</label>
                      <p class="lab-project-select-help">Only affects newly started conversations.</p>
                    </div>
                    <div class="lab-project-select-wrap">
                      <select id="lab-project-select" v-model="selectedHomeProjectId" class="lab-project-select">
                        <option value="">General OpenScience context</option>
                        <option v-for="project in openScienceSurfaces.runningProjects" :key="project.id" :value="project.id">
                          {{ project.name }}
                        </option>
                      </select>
                    </div>
                  </div>

                  <div class="lab-tabs-row">
                    <span class="lab-tabs-label">Browse</span>
                    <div class="lab-home-tabs" role="tablist" aria-label="Lab summary views">
                      <button
                        v-for="tab in labHomeTabs"
                        :key="tab.id"
                        class="lab-home-tab"
                        :class="{ 'is-active': activeLabHomeTab === tab.id }"
                        type="button"
                        role="tab"
                        :aria-selected="activeLabHomeTab === tab.id"
                        @click="activeLabHomeTab = tab.id"
                      >
                        {{ tab.label }}
                      </button>
                    </div>
                  </div>

                  <div
                    class="lab-home-summary"
                    :class="{ 'is-single-document': !activeLabDocumentList.length }"
                  >
                    <aside v-if="activeLabHomeTab === 'running'" class="lab-summary-list" aria-label="Running projects">
                      <button
                        v-for="project in openScienceSurfaces.runningProjects"
                        :key="project.id"
                        class="lab-summary-list-item"
                        :class="{ 'is-active': activeSummaryProjectId === project.id }"
                        type="button"
                        @click="activeSummaryProjectId = project.id"
                      >
                        <span>{{ project.name }}</span>
                        <small>{{ project.id }}</small>
                      </button>
                    </aside>
                    <aside v-else-if="activeLabHomeTab === 'past' && activeLabDocumentList.length" class="lab-summary-list" aria-label="Past projects">
                      <button
                        v-for="document in openScienceSurfaces.pastProjects"
                        :key="document.id"
                        class="lab-summary-list-item"
                        :class="{ 'is-active': activePastProjectId === document.id }"
                        type="button"
                        @click="activePastProjectId = document.id"
                      >
                        <span>{{ document.title }}</span>
                        <small>{{ document.id }}</small>
                      </button>
                    </aside>

                    <article class="lab-summary-document">
                      <div v-if="activeLabHomeTab === 'daily' && openScienceSurfaces.dailySummaries.length > 1" class="lab-summary-history">
                        <label class="lab-summary-history-label" for="daily-summary-select">Daily summary</label>
                        <select id="daily-summary-select" v-model="activeDailySummaryId" class="lab-summary-history-select">
                          <option
                            v-for="document in openScienceSurfaces.dailySummaries"
                            :key="document.id"
                            :value="document.id"
                          >
                            {{ document.title }}
                          </option>
                        </select>
                      </div>
                      <div v-if="activeLabDocument" class="lab-summary-document-header">
                        <div class="lab-summary-document-title">
                          <span>{{ activeLabDocument.title }}</span>
                          <small class="lab-summary-document-path" :title="activeLabDocument.path">
                            {{ activeLabDocument.path }}
                          </small>
                        </div>
                        <small v-if="activeLabDocument.updatedAtIso">{{ formatLabDocumentDate(activeLabDocument.updatedAtIso) }}</small>
                      </div>
                      <div v-if="isLoadingOpenScienceSurfaces" class="lab-summary-empty">Loading lab summaries...</div>
                      <div v-else-if="openScienceSurfaceError" class="lab-summary-empty">{{ openScienceSurfaceError }}</div>
                      <div v-else-if="activeLabDocument" class="lab-markdown" v-html="renderLabMarkdown(activeLabDocument.markdown)" />
                      <div v-else class="lab-summary-empty">{{ activeLabEmptyMessage }}</div>
                    </article>
                  </div>
                </section>

                <div v-if="selectedHomeProject" class="new-thread-project-context">
                  New conversations will include project context for {{ selectedHomeProject.name }}.
                </div>
              </div>

              <Teleport to="body">
                <div v-if="isLabReaderOpen" class="lab-reader-backdrop" @click="isLabReaderOpen = false">
                  <section class="lab-reader" role="dialog" aria-modal="true" aria-label="Lab summary reader" @click.stop>
                    <header class="lab-reader-header">
                      <div>
                        <p class="lab-reader-kicker">Lab summary</p>
                        <h2>{{ activeLabDocument?.title ?? 'Summary' }}</h2>
                        <p v-if="activeLabDocument" class="lab-reader-source" :title="activeLabDocument.path">
                          {{ activeLabDocument.path }}
                        </p>
                      </div>
                      <button class="lab-reader-close" type="button" @click="isLabReaderOpen = false">Close</button>
                    </header>
                    <div class="lab-reader-body">
                      <div v-if="activeLabDocument" class="lab-markdown" v-html="renderLabMarkdown(activeLabDocument.markdown)" />
                      <div v-else class="lab-summary-empty">{{ activeLabEmptyMessage }}</div>
                    </div>
                  </section>
                </div>
              </Teleport>

              <div class="composer-with-queue">
                <ThreadComposer ref="homeThreadComposerRef" :active-thread-id="composerThreadContextId"
                  :cwd="composerCwd"
                  :collaboration-modes="availableCollaborationModes"
                  :selected-collaboration-mode="selectedCollaborationMode"
                  :models="availableModelIds" :selected-model="selectedModelId"
                  :selected-reasoning-effort="selectedReasoningEffort"
                  :selected-speed-mode="selectedSpeedMode"
                  :is-updating-speed-mode="isUpdatingSpeedMode"
                  :skills="installedSkills"
                  :thread-token-usage="selectedThreadTokenUsage"
                  :codex-quota="codexQuota"
                  :is-turn-in-progress="false"
                  :is-interrupting-turn="false" :send-with-enter="sendWithEnter" :in-progress-submit-mode="inProgressSendMode"
                  :dictation-click-to-toggle="dictationClickToToggle" :dictation-auto-send="dictationAutoSend"
                  :dictation-language="dictationLanguage"
                  @submit="onSubmitThreadMessage"
                  @update:selected-collaboration-mode="onSelectCollaborationMode"
                  @update:selected-model="onSelectModel"
                  @update:selected-reasoning-effort="onSelectReasoningEffort"
                  @update:selected-speed-mode="onSelectSpeedMode" />
              </div>
            </div>
          </template>
          <template v-else>
            <div class="content-grid">
              <div class="content-thread">
                <ThreadConversation ref="threadConversationRef" :messages="filteredMessages" :is-loading="isLoadingMessages"
                  :active-thread-id="composerThreadContextId" :cwd="composerCwd" :scroll-state="selectedThreadScrollState"
                  :live-overlay="liveOverlay"
                  :pending-requests="selectedThreadServerRequests"
                  @update-scroll-state="onUpdateThreadScrollState"
                  @rollback="onRollback"
                  @respond-server-request="onRespondServerRequest" />
              </div>

              <div class="composer-with-queue">
                <QueuedMessages
                  :messages="selectedThreadQueuedMessages"
                  @edit="onEditQueuedMessage"
                  @steer="steerQueuedMessage"
                  @delete="removeQueuedMessage"
                />
                <ThreadPendingRequestPanel
                  v-if="selectedThreadPendingRequest"
                  :request="selectedThreadPendingRequest"
                  :request-count="selectedThreadServerRequests.length"
                  :has-queue-above="selectedThreadQueuedMessages.length > 0"
                  @respond-server-request="onRespondServerRequest"
                />
                <ThreadComposer v-else ref="threadComposerRef" :active-thread-id="composerThreadContextId"
                  :cwd="composerCwd"
                  :collaboration-modes="availableCollaborationModes"
                  :selected-collaboration-mode="selectedCollaborationMode"
                  :models="availableModelIds"
                  :selected-model="selectedModelId"
                  :selected-reasoning-effort="selectedReasoningEffort"
                  :selected-speed-mode="selectedSpeedMode"
                  :is-updating-speed-mode="isUpdatingSpeedMode"
                  :skills="installedSkills"
                  :thread-token-usage="selectedThreadTokenUsage"
                  :codex-quota="codexQuota"
                  :is-turn-in-progress="isSelectedThreadInProgress" :is-interrupting-turn="isInterruptingTurn"
                  :has-queue-above="selectedThreadQueuedMessages.length > 0"
                  :send-with-enter="sendWithEnter" :in-progress-submit-mode="inProgressSendMode"
                  :dictation-click-to-toggle="dictationClickToToggle" :dictation-auto-send="dictationAutoSend"
                  :dictation-language="dictationLanguage"
                  @update:selected-collaboration-mode="onSelectCollaborationMode"
                  @submit="onSubmitThreadMessage" @update:selected-model="onSelectModel"
                  @update:selected-reasoning-effort="onSelectReasoningEffort"
                  @update:selected-speed-mode="onSelectSpeedMode"
                  @interrupt="onInterruptTurn" />
              </div>
            </div>
          </template>
        </section>
      </section>
    </template>
  </DesktopLayout>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DesktopLayout from './components/layout/DesktopLayout.vue'
import SidebarThreadTree from './components/sidebar/SidebarThreadTree.vue'
import ContentHeader from './components/content/ContentHeader.vue'
import ThreadComposer from './components/content/ThreadComposer.vue'
import ThreadPendingRequestPanel from './components/content/ThreadPendingRequestPanel.vue'
import QueuedMessages from './components/content/QueuedMessages.vue'
import RateLimitStatus from './components/content/RateLimitStatus.vue'
import ComposerDropdown from './components/content/ComposerDropdown.vue'
import SidebarThreadControls from './components/sidebar/SidebarThreadControls.vue'
import IconTablerSearch from './components/icons/IconTablerSearch.vue'
import IconTablerSettings from './components/icons/IconTablerSettings.vue'
import IconTablerX from './components/icons/IconTablerX.vue'
import { useDesktopState } from './composables/useDesktopState'
import { useMobile } from './composables/useMobile'
import { renderMathToHtml, splitTextByMathSegments } from './utils/mathRendering'
import {
  configureTelegramBot,
  getAccounts,
  getOpenScienceSurfaces,
  getTelegramStatus,
  removeAccount,
  refreshAccountsFromAuth,
  searchThreads,
  switchAccount,
} from './api/codexGateway'
import type { ReasoningEffort, SpeedMode, ThreadScrollState, UiAccountEntry, UiRateLimitWindow, UiServerRequest, UiServerRequestReply, UiThreadTokenUsage } from './types/codex'
import type { ComposerDraftPayload, ThreadComposerExposed } from './components/content/ThreadComposer.vue'
import type { OpenScienceProjectSummary, OpenScienceSurfaceDocument, OpenScienceSurfaces, TelegramStatus } from './api/codexGateway'

const ThreadConversation = defineAsyncComponent(() => import('./components/content/ThreadConversation.vue'))
const SkillsHub = defineAsyncComponent(() => import('./components/content/SkillsHub.vue'))

const SIDEBAR_COLLAPSED_STORAGE_KEY = 'codex-web-local.sidebar-collapsed.v1'
const ACCOUNTS_SECTION_COLLAPSED_STORAGE_KEY = 'codex-web-local.accounts-section-collapsed.v1'
const appVersion = import.meta.env.VITE_APP_VERSION ?? 'unknown'
const DEFAULT_OPENSCIENCE_WORKSPACE = import.meta.env.VITE_DEFAULT_WORKSPACE_PATH?.trim() || '/Users/xulab/openscience/lab_assistant'
const SETTINGS_HELP = {
  sendWithEnter: 'When enabled, press Enter to send. When disabled, use Command+Enter to send.',
  inProgressSendMode: 'If the assistant is still working, choose whether a new message redirects the current task or waits in line.',
  appearance: 'Switch between system theme, light mode, and dark mode.',
  chatWidth: 'Choose how wide the conversation column and composer can grow on desktop screens.',
  dictationClickToToggle: 'Use click-to-start and click-to-stop dictation instead of hold-to-talk.',
  dictationAutoSend: 'Automatically send transcribed dictation when recording stops.',
  dictationLanguage: 'Choose transcription language or keep auto-detect.',
} as const

type ChatWidthMode = 'standard' | 'wide' | 'extra-wide'
type LabHomeTabId = 'running' | 'past' | 'daily'

type ChatWidthPreset = {
  label: string
  columnMax: string
  cardMax: string
}

const CHAT_WIDTH_PRESETS: Record<ChatWidthMode, ChatWidthPreset> = {
  standard: {
    label: 'Standard',
    columnMax: '45rem',
    cardMax: '76ch',
  },
  wide: {
    label: 'Wide',
    columnMax: '72rem',
    cardMax: '88ch',
  },
  'extra-wide': {
    label: 'Extra wide',
    columnMax: '96rem',
    cardMax: '96ch',
  },
}

const WHISPER_LANGUAGES: Record<string, string> = {
  en: 'english',
  zh: 'chinese',
  de: 'german',
  es: 'spanish',
  ru: 'russian',
  ko: 'korean',
  fr: 'french',
  ja: 'japanese',
  pt: 'portuguese',
  tr: 'turkish',
  pl: 'polish',
  ca: 'catalan',
  nl: 'dutch',
  ar: 'arabic',
  sv: 'swedish',
  it: 'italian',
  id: 'indonesian',
  hi: 'hindi',
  fi: 'finnish',
  vi: 'vietnamese',
  he: 'hebrew',
  uk: 'ukrainian',
  el: 'greek',
  ms: 'malay',
  cs: 'czech',
  ro: 'romanian',
  da: 'danish',
  hu: 'hungarian',
  ta: 'tamil',
  no: 'norwegian',
  th: 'thai',
  ur: 'urdu',
  hr: 'croatian',
  bg: 'bulgarian',
  lt: 'lithuanian',
  la: 'latin',
  mi: 'maori',
  ml: 'malayalam',
  cy: 'welsh',
  sk: 'slovak',
  te: 'telugu',
  fa: 'persian',
  lv: 'latvian',
  bn: 'bengali',
  sr: 'serbian',
  az: 'azerbaijani',
  sl: 'slovenian',
  kn: 'kannada',
  et: 'estonian',
  mk: 'macedonian',
  br: 'breton',
  eu: 'basque',
  is: 'icelandic',
  hy: 'armenian',
  ne: 'nepali',
  mn: 'mongolian',
  bs: 'bosnian',
  kk: 'kazakh',
  sq: 'albanian',
  sw: 'swahili',
  gl: 'galician',
  mr: 'marathi',
  pa: 'punjabi',
  si: 'sinhala',
  km: 'khmer',
  sn: 'shona',
  yo: 'yoruba',
  so: 'somali',
  af: 'afrikaans',
  oc: 'occitan',
  ka: 'georgian',
  be: 'belarusian',
  tg: 'tajik',
  sd: 'sindhi',
  gu: 'gujarati',
  am: 'amharic',
  yi: 'yiddish',
  lo: 'lao',
  uz: 'uzbek',
  fo: 'faroese',
  ht: 'haitian creole',
  ps: 'pashto',
  tk: 'turkmen',
  nn: 'nynorsk',
  mt: 'maltese',
  sa: 'sanskrit',
  lb: 'luxembourgish',
  my: 'myanmar',
  bo: 'tibetan',
  tl: 'tagalog',
  mg: 'malagasy',
  as: 'assamese',
  tt: 'tatar',
  haw: 'hawaiian',
  ln: 'lingala',
  ha: 'hausa',
  ba: 'bashkir',
  jw: 'javanese',
  su: 'sundanese',
  yue: 'cantonese',
}

const labHomeTabs: Array<{ id: LabHomeTabId; label: string }> = [
  { id: 'running', label: 'Running projects' },
  { id: 'past', label: 'Past projects' },
  { id: 'daily', label: 'Daily summary' },
]

const {
  projectGroups,
  projectDisplayNameById,
  selectedThread,
  selectedThreadTokenUsage,
  selectedThreadScrollState,
  selectedThreadServerRequests,
  selectedLiveOverlay,
  codexQuota,
  selectedThreadId,
  availableCollaborationModes,
  availableModelIds,
  selectedCollaborationMode,
  selectedModelId,
  selectedReasoningEffort,
  selectedSpeedMode,
  installedSkills,
  accountRateLimitSnapshots,
  messages,
  isLoadingThreads,
  isLoadingMessages,
  isSendingMessage,
  isInterruptingTurn,
  isUpdatingSpeedMode,
  refreshAll,
  refreshSkills,
  selectThread,
  ensureThreadMessagesLoaded,
  setThreadScrollState,
  archiveThreadById,
  renameThreadById,
  sendMessageToSelectedThread,
  sendMessageToNewThread,
  interruptSelectedThreadTurn,
  selectedThreadQueuedMessages,
  removeQueuedMessage,
  steerQueuedMessage,
  setSelectedCollaborationMode,
  setSelectedModelId,

  setSelectedReasoningEffort,
  updateSelectedSpeedMode,
  respondToPendingServerRequest,
  renameProject,
  removeProject,
  reorderProject,
  pinProjectToTop,
  startPolling,
  stopPolling,
  primeSelectedThread,
  rollbackSelectedThread,
} = useDesktopState()

const route = useRoute()
const router = useRouter()
const { isMobile } = useMobile()
const homeThreadComposerRef = ref<ThreadComposerExposed | null>(null)
const threadComposerRef = ref<ThreadComposerExposed | null>(null)
const threadConversationRef = ref<{ jumpToLatest: () => void } | null>(null)
const editingQueuedMessageState = ref<{ threadId: string; queueIndex: number } | null>(null)
const isRouteSyncInProgress = ref(false)
let hasPendingRouteSync = false
const hasInitialized = ref(false)
const newThreadCwd = ref(DEFAULT_OPENSCIENCE_WORKSPACE)
const isSidebarCollapsed = ref(loadSidebarCollapsed())
const sidebarSearchQuery = ref('')
const isSidebarSearchVisible = ref(false)
const sidebarSearchInputRef = ref<HTMLInputElement | null>(null)
const serverMatchedThreadIds = ref<string[] | null>(null)
let threadSearchTimer: ReturnType<typeof setTimeout> | null = null
const isSettingsOpen = ref(false)
const isAccountsSectionCollapsed = ref(loadAccountsSectionCollapsed())
const accounts = ref<UiAccountEntry[]>([])
const isRefreshingAccounts = ref(false)
const isSwitchingAccounts = ref(false)
const removingAccountId = ref('')
const confirmingRemoveAccountId = ref('')
const hoveredAccountId = ref('')
const accountActionError = ref('')
const SEND_WITH_ENTER_KEY = 'codex-web-local.send-with-enter.v1'
const IN_PROGRESS_SEND_MODE_KEY = 'codex-web-local.in-progress-send-mode.v1'
const DARK_MODE_KEY = 'codex-web-local.dark-mode.v1'
const DICTATION_CLICK_TO_TOGGLE_KEY = 'codex-web-local.dictation-click-to-toggle.v1'
const DICTATION_AUTO_SEND_KEY = 'codex-web-local.dictation-auto-send.v1'
const DICTATION_LANGUAGE_KEY = 'codex-web-local.dictation-language.v1'

const CHAT_WIDTH_KEY = 'codex-web-local.chat-width.v1'
const MOBILE_RESUME_RELOAD_MIN_HIDDEN_MS = 400
const sendWithEnter = ref(loadBoolPref(SEND_WITH_ENTER_KEY, true))
const inProgressSendMode = ref<'steer' | 'queue'>(loadInProgressSendModePref())
const darkMode = ref<'system' | 'light' | 'dark'>(loadDarkModePref())
const chatWidth = ref<ChatWidthMode>(loadChatWidthPref())
const dictationClickToToggle = ref(loadBoolPref(DICTATION_CLICK_TO_TOGGLE_KEY, false))
const dictationAutoSend = ref(loadBoolPref(DICTATION_AUTO_SEND_KEY, true))
const dictationLanguage = ref(loadDictationLanguagePref())
const dictationLanguageOptions = computed(() => buildDictationLanguageOptions())
const telegramStatus = ref<TelegramStatus>({
  configured: false,
  active: false,
  mappedChats: 0,
  mappedThreads: 0,
  lastError: '',
})
const mobileHiddenAtMs = ref<number | null>(null)
const mobileResumeReloadTriggered = ref(false)
const mobileResumeSyncInProgress = ref(false)
const activeLabHomeTab = ref<LabHomeTabId>('running')
const selectedHomeProjectId = ref('')
const activeSummaryProjectId = ref('')
const activePastProjectId = ref('')
const activeDailySummaryId = ref('')
const openScienceSurfaces = ref<OpenScienceSurfaces>({
  runningProjects: [],
  runningProjectDocs: [],
  pastProjects: [],
  dailySummaries: [],
  dailySummary: null,
})
const isLoadingOpenScienceSurfaces = ref(false)
const openScienceSurfaceError = ref('')
const isLabReaderOpen = ref(false)
let accountStatePollTimer: number | null = null
let isAccountStatePollInFlight = false

const routeThreadId = computed(() => {
  const rawThreadId = route.params.threadId
  return typeof rawThreadId === 'string' ? rawThreadId : ''
})

const knownThreadIdSet = computed(() => {
  const ids = new Set<string>()
  for (const group of projectGroups.value) {
    for (const thread of group.threads) {
      ids.add(thread.id)
    }
  }
  return ids
})

const isHomeRoute = computed(() => route.name === 'home')
const isSkillsRoute = computed(() => route.name === 'skills')
const contentTitle = computed(() => {
  if (isSkillsRoute.value) return 'Capabilities'
  if (isHomeRoute.value) return 'New request'
  return selectedThread.value?.title ?? 'Choose a conversation'
})
const browserHostName =
  typeof window !== 'undefined'
    ? (window.location.hostname || window.location.host || 'codexui')
    : 'codexui'
const pageTitle = computed(() => {
  const threadTitle = selectedThread.value?.title?.trim() ?? ''
  return threadTitle || browserHostName
})
const filteredMessages = computed(() =>
  messages.value.filter((message) => {
    const type = normalizeMessageType(message.messageType, message.role)
    if (type === 'worked') return true
    if (type === 'turnActivity.live' || type === 'turnError.live' || type === 'agentReasoning.live') return false
    return true
  }),
)
const latestUserTurnId = computed(() => {
  for (let index = messages.value.length - 1; index >= 0; index -= 1) {
    const message = messages.value[index]
    if (message.role !== 'user') continue
    const turnId = message.turnId?.trim() ?? ''
    if (turnId.length > 0) return turnId
  }
  return ''
})
const liveOverlay = computed(() => selectedLiveOverlay.value)
const composerThreadContextId = computed(() => (isHomeRoute.value ? '__new-thread__' : selectedThreadId.value))
const selectedThreadPendingRequest = computed<UiServerRequest | null>(() => {
  const rows = selectedThreadServerRequests.value
  return rows.length > 0 ? rows[rows.length - 1] : null
})
const composerCwd = computed(() => {
  if (isHomeRoute.value) return newThreadCwd.value.trim()
  return selectedThread.value?.cwd?.trim() ?? ''
})
const isSelectedThreadInProgress = computed(() => !isHomeRoute.value && selectedThread.value?.inProgress === true)
const showThreadContextBadge = computed(() => !isHomeRoute.value && !isSkillsRoute.value && selectedThreadId.value.trim().length > 0)
const isAccountSwitchBlocked = computed(() =>
  isSendingMessage.value ||
  isInterruptingTurn.value ||
  isSelectedThreadInProgress.value ||
  selectedThreadServerRequests.value.length > 0,
)

function formatCompactTokenCount(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return new Intl.NumberFormat('en-US', {
    notation: value >= 1000 ? 'compact' : 'standard',
    maximumFractionDigits: value >= 100000 ? 0 : 1,
  }).format(Math.max(0, Math.trunc(value)))
}

function buildThreadContextTooltip(usage: UiThreadTokenUsage | null): string {
  if (!usage) {
    return 'Waiting for Codex thread/tokenUsage/updated events for this thread.'
  }

  const lines = [
    `Current context usage: ${usage.currentContextTokens.toLocaleString()} tokens`,
    `Cumulative thread usage: ${usage.total.totalTokens.toLocaleString()} tokens`,
  ]

  if (typeof usage.modelContextWindow === 'number') {
    lines.unshift(`Model context window: ${usage.modelContextWindow.toLocaleString()} tokens`)
    lines.push(`Remaining context: ${(usage.remainingContextTokens ?? 0).toLocaleString()} tokens`)
  } else {
    lines.push('Model context window is unavailable in the latest usage event.')
  }

  return lines.join('\n')
}

const threadContextBadgeState = computed(() => {
  const remainingPercent = selectedThreadTokenUsage.value?.remainingContextPercent
  if (remainingPercent === null || typeof remainingPercent !== 'number') return 'pending'
  if (remainingPercent <= 10) return 'danger'
  if (remainingPercent <= 25) return 'warning'
  return 'ok'
})

const threadContextPrimaryText = computed(() => {
  const usage = selectedThreadTokenUsage.value
  if (!usage) return 'Awaiting data'
  if (typeof usage.remainingContextTokens === 'number') {
    return `${formatCompactTokenCount(usage.remainingContextTokens)} left`
  }
  return `${formatCompactTokenCount(usage.currentContextTokens)} used`
})

const threadContextSecondaryText = computed(() => {
  const usage = selectedThreadTokenUsage.value
  if (!usage) return 'Updates after the next token usage event'
  if (typeof usage.modelContextWindow === 'number') {
    return `${formatCompactTokenCount(usage.currentContextTokens)} used / ${formatCompactTokenCount(usage.modelContextWindow)}`
  }
  return 'Window size unavailable'
})

const threadContextTooltip = computed(() => buildThreadContextTooltip(selectedThreadTokenUsage.value))
const darkModeMediaQuery = typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null
const chatWidthLabel = computed(() => CHAT_WIDTH_PRESETS[chatWidth.value].label)
const contentStyle = computed(() => {
  const preset = CHAT_WIDTH_PRESETS[chatWidth.value]
  return {
    '--chat-column-max': preset.columnMax,
    '--chat-card-max': preset.cardMax,
  }
})
const telegramStatusText = computed(() => {
  if (!telegramStatus.value.configured) return 'Not configured'
  const base = telegramStatus.value.active ? 'Online' : 'Configured (offline)'
  const mapped = `${telegramStatus.value.mappedChats} chat(s), ${telegramStatus.value.mappedThreads} thread(s)`
  const error = telegramStatus.value.lastError ? `, error: ${telegramStatus.value.lastError}` : ''
  return `${base}, ${mapped}${error}`
})
const selectedHomeProject = computed<OpenScienceProjectSummary | null>(() => (
  openScienceSurfaces.value.runningProjects.find((project) => project.id === selectedHomeProjectId.value) ?? null
))
const activeSummaryProjectDocument = computed<OpenScienceSurfaceDocument | null>(() => {
  const docs = openScienceSurfaces.value.runningProjectDocs
  const activeId = activeSummaryProjectId.value || selectedHomeProjectId.value || docs[0]?.id || ''
  return docs.find((document) => document.id === activeId) ?? docs[0] ?? null
})
const activePastProjectDocument = computed<OpenScienceSurfaceDocument | null>(() => {
  const docs = openScienceSurfaces.value.pastProjects
  const activeId = activePastProjectId.value || docs[0]?.id || ''
  return docs.find((document) => document.id === activeId) ?? docs[0] ?? null
})
const activeDailySummaryDocument = computed<OpenScienceSurfaceDocument | null>(() => {
  const docs = openScienceSurfaces.value.dailySummaries
  const activeId = activeDailySummaryId.value || openScienceSurfaces.value.dailySummary?.id || docs[0]?.id || ''
  return docs.find((document) => document.id === activeId) ?? openScienceSurfaces.value.dailySummary ?? docs[0] ?? null
})
const activeLabDocumentList = computed<OpenScienceSurfaceDocument[]>(() => {
  if (activeLabHomeTab.value === 'running') return openScienceSurfaces.value.runningProjectDocs
  if (activeLabHomeTab.value === 'past') return openScienceSurfaces.value.pastProjects
  return []
})
const activeLabDocument = computed<OpenScienceSurfaceDocument | null>(() => {
  if (activeLabHomeTab.value === 'running') return activeSummaryProjectDocument.value
  if (activeLabHomeTab.value === 'daily') return activeDailySummaryDocument.value
  return activePastProjectDocument.value
})
const activeLabEmptyMessage = computed(() => {
  if (activeLabHomeTab.value === 'daily') return 'No daily overview has been generated yet.'
  if (activeLabHomeTab.value === 'past') return 'Past-project summaries will appear here as they are promoted.'
  return 'No running-project summaries were found.'
})
function formatLabDocumentDate(value: string): string {
  const timestamp = Date.parse(value)
  if (!Number.isFinite(timestamp)) return ''
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(timestamp))
}

onMounted(() => {
  window.addEventListener('keydown', onWindowKeyDown)
  document.addEventListener('visibilitychange', onDocumentVisibilityChange)
  window.addEventListener('pageshow', onWindowPageShow)
  window.addEventListener('focus', onWindowFocus)
  applyDarkMode()
  darkModeMediaQuery?.addEventListener('change', applyDarkMode)
  void initialize()
  void refreshTelegramStatus()
  void loadOpenScienceSurfaces()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onWindowKeyDown)
  document.removeEventListener('visibilitychange', onDocumentVisibilityChange)
  window.removeEventListener('pageshow', onWindowPageShow)
  window.removeEventListener('focus', onWindowFocus)
  darkModeMediaQuery?.removeEventListener('change', applyDarkMode)
  if (accountStatePollTimer !== null) {
    window.clearInterval(accountStatePollTimer)
    accountStatePollTimer = null
  }
  if (threadSearchTimer) {
    clearTimeout(threadSearchTimer)
    threadSearchTimer = null
  }
  stopPolling()
})

watch(sidebarSearchQuery, (value) => {
  const query = value.trim()
  if (threadSearchTimer) {
    clearTimeout(threadSearchTimer)
    threadSearchTimer = null
  }
  if (!query) {
    serverMatchedThreadIds.value = null
    return
  }

  threadSearchTimer = setTimeout(() => {
    void searchThreads(query, 1000)
      .then((result) => {
        if (sidebarSearchQuery.value.trim() !== query) return
        serverMatchedThreadIds.value = result.threadIds
      })
      .catch(() => {
        if (sidebarSearchQuery.value.trim() !== query) return
        serverMatchedThreadIds.value = null
      })
  }, 220)
})

watch(selectedHomeProjectId, (projectId) => {
  if (!projectId) return
  if (openScienceSurfaces.value.runningProjectDocs.some((document) => document.id === projectId)) {
    activeSummaryProjectId.value = projectId
  }
})

watch(accounts, () => {
  if (typeof window === 'undefined') return
  const shouldPoll = accounts.value.some((account) => account.quotaStatus === 'loading')
  if (!shouldPoll) {
    if (accountStatePollTimer !== null) {
      window.clearInterval(accountStatePollTimer)
      accountStatePollTimer = null
    }
    return
  }
  if (accountStatePollTimer !== null) return
  accountStatePollTimer = window.setInterval(() => {
    if (isAccountStatePollInFlight) return
    isAccountStatePollInFlight = true
    void loadAccountsState({ silent: true }).finally(() => {
      isAccountStatePollInFlight = false
    })
  }, 1500)
}, { deep: true })

function onSkillsChanged(): void {
  void refreshSkills()
}

async function refreshTelegramStatus(): Promise<void> {
  try {
    telegramStatus.value = await getTelegramStatus()
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load Telegram status'
    telegramStatus.value = {
      configured: false,
      active: false,
      mappedChats: 0,
      mappedThreads: 0,
      lastError: message,
    }
  }
}

function toggleSidebarSearch(): void {
  isSidebarSearchVisible.value = !isSidebarSearchVisible.value
  if (isSidebarSearchVisible.value) {
    nextTick(() => sidebarSearchInputRef.value?.focus())
  } else {
    sidebarSearchQuery.value = ''
  }
}

function clearSidebarSearch(): void {
  sidebarSearchQuery.value = ''
  sidebarSearchInputRef.value?.focus()
}

function onSidebarSearchKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    isSidebarSearchVisible.value = false
    sidebarSearchQuery.value = ''
  }
}

function onSelectThread(threadId: string): void {
  if (!threadId) return
  if (route.name === 'thread' && routeThreadId.value === threadId) return
  void router.push({ name: 'thread', params: { threadId } })
  if (isMobile.value) setSidebarCollapsed(true)
}

async function onExportThread(threadId: string): Promise<void> {
  if (!threadId) return
  if (selectedThreadId.value !== threadId) {
    await selectThread(threadId)
    await router.push({ name: 'thread', params: { threadId } })
  }
  await nextTick()
  onExportChat()
}

function shortAccountId(accountId: string): string {
  return accountId.length > 8 ? accountId.slice(-8) : accountId
}

function formatAccountMeta(account: UiAccountEntry): string {
  const segments = [account.planType || 'unknown']
  if (account.authMode) {
    segments.unshift(account.authMode)
  }
  return segments.join(' · ')
}

function isPaymentRequiredErrorMessage(value: string | null): boolean {
  if (!value) return false
  const normalized = value.toLowerCase()
  return normalized.includes('payment required') || /\b402\b/.test(normalized)
}

function isAccountUnavailable(account: UiAccountEntry): boolean {
  return account.unavailableReason === 'payment_required' || isPaymentRequiredErrorMessage(account.quotaError)
}

function isAccountActionDisabled(account: UiAccountEntry): boolean {
  return isRefreshingAccounts.value || isSwitchingAccounts.value || removingAccountId.value.length > 0
    || (account.isActive && removingAccountId.value !== account.accountId && isAccountSwitchBlocked.value)
}

function isRemoveConfirmationActive(account: UiAccountEntry): boolean {
  return confirmingRemoveAccountId.value === account.accountId
}

function isRemoveVisible(account: UiAccountEntry): boolean {
  return hoveredAccountId.value === account.accountId || isRemoveConfirmationActive(account)
}

function getAccountSwitchLabel(account: UiAccountEntry): string {
  if (isAccountUnavailable(account)) return 'Unavailable'
  if (account.isActive) return 'Active'
  if (isSwitchingAccounts.value) return 'Switching…'
  return 'Switch'
}

function getAccountRemoveLabel(account: UiAccountEntry): string {
  if (removingAccountId.value === account.accountId) return 'Removing…'
  if (isRemoveConfirmationActive(account)) return 'Click again to remove'
  return 'Remove'
}

function onAccountCardPointerEnter(accountId: string): void {
  hoveredAccountId.value = accountId
}

function onAccountCardPointerLeave(accountId: string): void {
  if (hoveredAccountId.value === accountId) {
    hoveredAccountId.value = ''
  }
  if (removingAccountId.value === accountId) return
  if (confirmingRemoveAccountId.value === accountId) {
    confirmingRemoveAccountId.value = ''
  }
}

function pickWeeklyQuotaWindow(account: UiAccountEntry) {
  const quota = account.quotaSnapshot
  if (!quota) return null
  const windows = [quota?.primary, quota?.secondary].filter((quotaWindow): quotaWindow is UiRateLimitWindow => quotaWindow !== null)
  const exactWeekly = windows.find((quotaWindow) => quotaWindow.windowMinutes === 7 * 24 * 60)
  if (exactWeekly) {
    return exactWeekly
  }
  const longerWindow = windows
    .filter((quotaWindow) => typeof quotaWindow.windowMinutes === 'number' && quotaWindow.windowMinutes >= 7 * 24 * 60)
    .sort((first, second) => (first.windowMinutes ?? 0) - (second.windowMinutes ?? 0))[0] ?? null
  if (longerWindow) {
    return longerWindow
  }
  return quota.secondary ?? null
}

function formatResetDateCompact(resetsAt: number | null): string {
  if (typeof resetsAt !== 'number' || !Number.isFinite(resetsAt)) return ''
  const date = new Date(resetsAt * 1000)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function formatAccountQuota(account: UiAccountEntry): string {
  if (isAccountUnavailable(account)) {
    return account.quotaError || '402 Payment Required'
  }
  const quota = account.quotaSnapshot
  const window = pickWeeklyQuotaWindow(account)
  const fallbackWindow = quota?.primary ?? quota?.secondary ?? null
  const displayWindow = window ?? fallbackWindow
  if (displayWindow) {
    const remainingPercent = Math.max(0, Math.min(100, 100 - Math.round(displayWindow.usedPercent)))
    const refreshDate = formatResetDateCompact(displayWindow.resetsAt)
    return refreshDate
      ? `${remainingPercent}% weekly remaining · ${refreshDate}`
      : `${remainingPercent}% weekly remaining`
  }
  if (quota?.credits?.unlimited) {
    return 'Unlimited credits'
  }
  if (quota?.credits?.hasCredits && quota.credits.balance) {
    return `${quota.credits.balance} credits`
  }
  if (account.quotaStatus === 'loading') {
    return 'Loading quota…'
  }
  if (account.quotaStatus === 'error') {
    return account.quotaError || 'Quota unavailable'
  }
  if (account.quotaStatus === 'ready' || account.quotaStatus === 'idle') {
    return 'Quota unavailable'
  }
  return 'Fetching account details…'
}

function buildAccountTitle(account: UiAccountEntry): string {
  return [
    account.email || 'Account',
    formatAccountMeta(account),
    isAccountUnavailable(account) ? 'Unavailable account' : null,
    formatAccountQuota(account),
    `Workspace ${account.accountId}`,
  ].filter(Boolean).join('\n')
}

async function loadAccountsState(options: { silent?: boolean } = {}): Promise<void> {
  try {
    const result = await getAccounts()
    accounts.value = result.accounts
    if (!result.accounts.some((account) => account.accountId === hoveredAccountId.value)) {
      hoveredAccountId.value = ''
    }
    if (!result.accounts.some((account) => account.accountId === confirmingRemoveAccountId.value)) {
      confirmingRemoveAccountId.value = ''
    }
  } catch (error) {
    if (options.silent === true) return
    accountActionError.value = error instanceof Error ? error.message : 'Failed to load accounts'
  }
}

async function onRefreshAccounts(): Promise<void> {
  if (isRefreshingAccounts.value || isSwitchingAccounts.value) return
  accountActionError.value = ''
  hoveredAccountId.value = ''
  confirmingRemoveAccountId.value = ''
  isRefreshingAccounts.value = true
  try {
    const result = await refreshAccountsFromAuth()
    accounts.value = result.accounts
    stopPolling()
    startPolling()
    void refreshAll({
      includeSelectedThreadMessages: true,
    })
  } catch (error) {
    accountActionError.value = error instanceof Error ? error.message : 'Failed to refresh accounts'
  } finally {
    isRefreshingAccounts.value = false
  }
}

async function onSwitchAccount(accountId: string): Promise<void> {
  if (isSwitchingAccounts.value || isRefreshingAccounts.value) return
  if (isAccountSwitchBlocked.value) {
    accountActionError.value = 'Finish the current turn and pending requests before switching accounts.'
    return
  }
  accountActionError.value = ''
  hoveredAccountId.value = ''
  confirmingRemoveAccountId.value = ''
  isSwitchingAccounts.value = true
  try {
    const nextActiveAccount = await switchAccount(accountId)
    accounts.value = accounts.value.map((account) => (
      account.accountId === accountId
        ? nextActiveAccount
        : { ...account, isActive: false }
    ))
    stopPolling()
    startPolling()
    void refreshAll({
      includeSelectedThreadMessages: true,
    })
    void loadAccountsState({ silent: true })
  } catch (error) {
    accountActionError.value = error instanceof Error ? error.message : 'Failed to switch account'
  } finally {
    isSwitchingAccounts.value = false
  }
}

async function onRemoveAccount(accountId: string): Promise<void> {
  if (isRefreshingAccounts.value || isSwitchingAccounts.value || removingAccountId.value.length > 0) return
  const targetAccount = accounts.value.find((account) => account.accountId === accountId) ?? null
  if (!targetAccount) return
  if (confirmingRemoveAccountId.value !== accountId) {
    confirmingRemoveAccountId.value = accountId
    return
  }
  if (targetAccount.isActive && isAccountSwitchBlocked.value) {
    accountActionError.value = 'Finish the current turn and pending requests before removing the active account.'
    return
  }

  const removedWasActive = targetAccount.isActive
  accountActionError.value = ''
  confirmingRemoveAccountId.value = ''
  removingAccountId.value = accountId
  try {
    const result = await removeAccount(accountId)
    accounts.value = result.accounts
    stopPolling()
    startPolling()
    if (removedWasActive) {
      void refreshAll({
        includeSelectedThreadMessages: true,
      })
    }
    void loadAccountsState({ silent: true })
  } catch (error) {
    accountActionError.value = error instanceof Error ? error.message : 'Failed to remove account'
  } finally {
    removingAccountId.value = ''
  }
}

function onArchiveThread(threadId: string): void {
  void archiveThreadById(threadId)
}

function onStartNewThread(projectName: string): void {
  if (isMobile.value) setSidebarCollapsed(true)
  if (isHomeRoute.value) return
  void router.push({ name: 'home' })
}

function onStartNewThreadFromToolbar(): void {
  if (isMobile.value) setSidebarCollapsed(true)
  if (isHomeRoute.value) return
  void router.push({ name: 'home' })
}

function onRenameProject(payload: { projectName: string; displayName: string }): void {
  renameProject(payload.projectName, payload.displayName)
}

function onRenameThread(payload: { threadId: string; title: string }): void {
  void renameThreadById(payload.threadId, payload.title)
}

async function onRemoveProject(projectName: string): Promise<void> {
  await removeProject(projectName)
}

function onReorderProject(payload: { projectName: string; toIndex: number }): void {
  reorderProject(payload.projectName, payload.toIndex)
}

function onUpdateThreadScrollState(payload: { threadId: string; state: ThreadScrollState }): void {
  setThreadScrollState(payload.threadId, payload.state)
}

function onRespondServerRequest(payload: UiServerRequestReply): void {
  void handleServerRequestResponse(payload)
}

async function handleServerRequestResponse(payload: UiServerRequestReply): Promise<void> {
  const responded = await respondToPendingServerRequest(payload)
  const followUpMessageText = payload.followUpMessageText?.trim() ?? ''
  if (!responded || !followUpMessageText || isHomeRoute.value) return

  try {
    await sendMessageToSelectedThread(followUpMessageText, [], [], 'steer', [])
  } catch {
    // sendMessageToSelectedThread already surfaces the error through shared state.
  }
}

function setSidebarCollapsed(nextValue: boolean): void {
  if (isSidebarCollapsed.value === nextValue) return
  isSidebarCollapsed.value = nextValue
  saveSidebarCollapsed(nextValue)
}

function onWindowKeyDown(event: KeyboardEvent): void {
  if (event.defaultPrevented) return
  if (!event.ctrlKey && !event.metaKey) return
  if (event.shiftKey || event.altKey) return
  if (event.key.toLowerCase() !== 'b') return
  event.preventDefault()
  setSidebarCollapsed(!isSidebarCollapsed.value)
}

function onDocumentVisibilityChange(): void {
  if (typeof document === 'undefined') return
  if (!isMobile.value) return

  if (document.visibilityState === 'hidden') {
    mobileHiddenAtMs.value = Date.now()
    mobileResumeReloadTriggered.value = false
    return
  }

  maybeSyncAfterMobileResume()
}

function onWindowPageShow(event: PageTransitionEvent): void {
  if (!event.persisted) return
  maybeSyncAfterMobileResume()
}

function onWindowFocus(): void {
  maybeSyncAfterMobileResume()
}

function maybeSyncAfterMobileResume(): void {
  if (typeof window === 'undefined' || typeof document === 'undefined') return
  if (!isMobile.value) return
  if (document.visibilityState !== 'visible') return
  if (mobileResumeReloadTriggered.value) return
  if (mobileHiddenAtMs.value === null) return

  const hiddenForMs = Date.now() - mobileHiddenAtMs.value
  if (hiddenForMs < MOBILE_RESUME_RELOAD_MIN_HIDDEN_MS) return

  mobileResumeReloadTriggered.value = true
  mobileHiddenAtMs.value = null
  void syncAfterMobileResume()
}

async function syncAfterMobileResume(): Promise<void> {
  if (mobileResumeSyncInProgress.value) return
  mobileResumeSyncInProgress.value = true

  try {
    await refreshAll({
      includeSelectedThreadMessages: true,
      awaitAncillaryRefreshes: true,
    })
    await syncThreadSelectionWithRoute()
  } finally {
    mobileResumeSyncInProgress.value = false
  }
}

function onSubmitThreadMessage(payload: { text: string; imageUrls: string[]; fileAttachments: Array<{ label: string; path: string; fsPath: string }>; skills: Array<{ name: string; path: string }>; mode: 'steer' | 'queue' }): void {
  const text = payload.text
  scheduleMobileConversationJumpToLatest()
  const editingState = editingQueuedMessageState.value
  const queueInsertIndex =
    payload.mode === 'queue'
    && editingState
    && editingState.threadId === selectedThreadId.value
      ? editingState.queueIndex
      : undefined
  editingQueuedMessageState.value = null
  if (isHomeRoute.value) {
    void submitFirstMessageForNewThread(text, payload.imageUrls, payload.skills, payload.fileAttachments)
    return
  }
  void sendMessageToSelectedThread(text, payload.imageUrls, payload.skills, payload.mode, payload.fileAttachments, queueInsertIndex)
}

function onConnectTelegramBot(): void {
  if (typeof window === 'undefined') return
  const botToken = window.prompt('Telegram bot token')
  if (!botToken || !botToken.trim()) return

  void configureTelegramBot(botToken.trim())
    .then(() => {
      window.alert('Telegram bot configured. Open the bot DM and send /start.')
      void refreshTelegramStatus()
    })
    .catch((error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to connect Telegram bot'
      window.alert(message)
      void refreshTelegramStatus()
    })
}

function onEditQueuedMessage(messageId: string): void {
  const queueIndex = selectedThreadQueuedMessages.value.findIndex((item) => item.id === messageId)
  const message = queueIndex >= 0 ? selectedThreadQueuedMessages.value[queueIndex] : undefined
  const composer = threadComposerRef.value
  if (!message || !composer) return

  if (composer.hasUnsavedDraft()) {
    const shouldReplace = window.confirm('Replace the current draft with this queued message for editing?')
    if (!shouldReplace) return
  }

  editingQueuedMessageState.value = selectedThreadId.value
    ? { threadId: selectedThreadId.value, queueIndex }
    : null
  const payload: ComposerDraftPayload = {
    text: message.text,
    imageUrls: [...message.imageUrls],
    fileAttachments: message.fileAttachments.map((attachment) => ({ ...attachment })),
    skills: message.skills.map((skill) => ({ ...skill })),
  }
  composer.hydrateDraft(payload)
  removeQueuedMessage(messageId)
}


function scheduleMobileConversationJumpToLatest(): void {
  if (!isMobile.value || isHomeRoute.value) return

  const jumpToLatest = () => {
    threadConversationRef.value?.jumpToLatest()
  }

  jumpToLatest()
  void nextTick(() => {
    jumpToLatest()
    if (typeof window === 'undefined') return
    window.requestAnimationFrame(() => {
      jumpToLatest()
      window.requestAnimationFrame(jumpToLatest)
    })
  })
}

function onSelectModel(modelId: string): void {
  setSelectedModelId(modelId)
}

function onSelectReasoningEffort(effort: ReasoningEffort | ''): void {
  setSelectedReasoningEffort(effort)
}

function onSelectSpeedMode(mode: SpeedMode): void {
  void updateSelectedSpeedMode(mode)
}

function onInterruptTurn(): void {
  void interruptSelectedThreadTurn()
}

function onRollback(payload: { turnId: string }): void {
  const targetTurnId = payload.turnId.trim()
  if (targetTurnId.length > 0) {
    const rollbackUserMessage = [...filteredMessages.value]
      .reverse()
      .find((message) => (
        message.role === 'user'
        && (message.turnId?.trim() ?? '') === targetTurnId
        && message.text.trim().length > 0
      ))
    if (rollbackUserMessage?.text && threadComposerRef.value) {
      threadComposerRef.value.appendTextToDraft(rollbackUserMessage.text)
    }
  }
  void rollbackSelectedThread(payload.turnId)
}


function onExportChat(): void {
  if (isHomeRoute.value || isSkillsRoute.value || typeof document === 'undefined') return
  if (!selectedThread.value || filteredMessages.value.length === 0) return
  const markdown = buildThreadMarkdown()
  const fileName = buildExportFileName()
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}

function buildThreadMarkdown(): string {
  const lines: string[] = []
  const threadTitle = selectedThread.value?.title?.trim() || 'Untitled thread'
  lines.push(`# ${escapeMarkdownText(threadTitle)}`)
  lines.push('')
  lines.push(`- Exported: ${new Date().toISOString()}`)
  lines.push(`- Thread ID: ${selectedThread.value?.id ?? ''}`)
  lines.push('')
  lines.push('---')
  lines.push('')

  for (const message of filteredMessages.value) {
    const roleLabel = message.role ? message.role.toUpperCase() : 'MESSAGE'
    lines.push(`## ${roleLabel}`)
    lines.push('')

    const normalizedText = message.text.trim()
    if (normalizedText) {
      lines.push(normalizedText)
      lines.push('')
    }

    if (message.commandExecution) {
      lines.push('```text')
      lines.push(`command: ${message.commandExecution.command}`)
      lines.push(`status: ${message.commandExecution.status}`)
      if (message.commandExecution.cwd) {
        lines.push(`cwd: ${message.commandExecution.cwd}`)
      }
      if (message.commandExecution.exitCode !== null) {
        lines.push(`exitCode: ${message.commandExecution.exitCode}`)
      }
      lines.push(message.commandExecution.aggregatedOutput || '(no output)')
      lines.push('```')
      lines.push('')
    }

    if (message.fileAttachments && message.fileAttachments.length > 0) {
      lines.push('Attachments:')
      for (const attachment of message.fileAttachments) {
        lines.push(`- ${attachment.path}`)
      }
      lines.push('')
    }

    if (message.images && message.images.length > 0) {
      lines.push('Images:')
      for (const imageUrl of message.images) {
        lines.push(`- ${imageUrl}`)
      }
      lines.push('')
    }
  }

  return `${lines.join('\n').trimEnd()}\n`
}

function buildExportFileName(): string {
  const threadTitle = selectedThread.value?.title?.trim() || 'chat'
  const sanitized = threadTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  const base = sanitized || 'chat'
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  return `${base}-${stamp}.md`
}

function escapeMarkdownText(value: string): string {
  return value.replace(/([\\`*_{}\[\]()#+\-.!])/g, '\\$1')
}

function loadBoolPref(key: string, fallback: boolean): boolean {
  if (typeof window === 'undefined') return fallback
  const v = window.localStorage.getItem(key)
  if (v === null) return fallback
  return v === '1'
}

function loadDarkModePref(): 'system' | 'light' | 'dark' {
  if (typeof window === 'undefined') return 'system'
  const v = window.localStorage.getItem(DARK_MODE_KEY)
  if (v === 'light' || v === 'dark') return v
  return 'system'
}

function loadInProgressSendModePref(): 'steer' | 'queue' {
  if (typeof window === 'undefined') return 'steer'
  const v = window.localStorage.getItem(IN_PROGRESS_SEND_MODE_KEY)
  return v === 'queue' ? 'queue' : 'steer'
}

function loadChatWidthPref(): ChatWidthMode {
  if (typeof window === 'undefined') return 'standard'
  const value = window.localStorage.getItem(CHAT_WIDTH_KEY)
  return value === 'standard' || value === 'wide' || value === 'extra-wide' ? value : 'standard'
}

function toggleSendWithEnter(): void {
  sendWithEnter.value = !sendWithEnter.value
  window.localStorage.setItem(SEND_WITH_ENTER_KEY, sendWithEnter.value ? '1' : '0')
}

function cycleInProgressSendMode(): void {
  inProgressSendMode.value = inProgressSendMode.value === 'steer' ? 'queue' : 'steer'
  window.localStorage.setItem(IN_PROGRESS_SEND_MODE_KEY, inProgressSendMode.value)
}

function cycleDarkMode(): void {
  const order: Array<'system' | 'light' | 'dark'> = ['system', 'light', 'dark']
  const idx = order.indexOf(darkMode.value)
  darkMode.value = order[(idx + 1) % order.length]
  window.localStorage.setItem(DARK_MODE_KEY, darkMode.value)
  applyDarkMode()
}

function cycleChatWidth(): void {
  const order: ChatWidthMode[] = ['standard', 'wide', 'extra-wide']
  const idx = order.indexOf(chatWidth.value)
  chatWidth.value = order[(idx + 1) % order.length]
  window.localStorage.setItem(CHAT_WIDTH_KEY, chatWidth.value)
}

function toggleDictationClickToToggle(): void {
  dictationClickToToggle.value = !dictationClickToToggle.value
  window.localStorage.setItem(DICTATION_CLICK_TO_TOGGLE_KEY, dictationClickToToggle.value ? '1' : '0')
}

function toggleDictationAutoSend(): void {
  dictationAutoSend.value = !dictationAutoSend.value
  window.localStorage.setItem(DICTATION_AUTO_SEND_KEY, dictationAutoSend.value ? '1' : '0')
}
function onDictationLanguageChange(nextValue: string): void {
  const normalized = normalizeToWhisperLanguage(nextValue.trim())
  const value = normalized || 'auto'
  dictationLanguage.value = value
  window.localStorage.setItem(DICTATION_LANGUAGE_KEY, value)
}

function loadDictationLanguagePref(): string {
  if (typeof window === 'undefined') return 'auto'
  const value = window.localStorage.getItem(DICTATION_LANGUAGE_KEY)?.trim() || 'auto'
  const normalized = normalizeToWhisperLanguage(value)
  return normalized || 'auto'
}

function buildDictationLanguageOptions(): Array<{ value: string; label: string }> {
  const options: Array<{ value: string; label: string }> = [{ value: 'auto', label: 'Auto-detect' }]
  const seen = new Set<string>(['auto'])
  function formatLanguageLabel(value: string): string {
    const languageName = WHISPER_LANGUAGES[value] || value
    const title = languageName.charAt(0).toUpperCase() + languageName.slice(1)
    return `${title} (${value})`
  }

  for (const raw of typeof navigator !== 'undefined' ? (navigator.languages ?? []) : []) {
    const value = normalizeToWhisperLanguage(raw)
    if (!value || seen.has(value)) continue
    seen.add(value)
    options.push({
      value,
      label: `Preferred: ${formatLanguageLabel(value)}`,
    })
  }

  for (const value of Object.keys(WHISPER_LANGUAGES)) {
    if (seen.has(value)) continue
    seen.add(value)
    options.push({
      value,
      label: formatLanguageLabel(value),
    })
  }

  const current = dictationLanguage.value.trim()
  if (current && !seen.has(current)) {
    options.push({
      value: current,
      label: formatLanguageLabel(current),
    })
  }

  return options
}

function normalizeToWhisperLanguage(raw: string): string {
  const value = raw.trim().toLowerCase()
  if (!value || value === 'auto') return ''
  if (value in WHISPER_LANGUAGES) return value
  const base = value.split('-')[0] ?? value
  if (base in WHISPER_LANGUAGES) return base
  return ''
}

function applyDarkMode(): void {
  const root = document.documentElement
  if (darkMode.value === 'dark') {
    root.classList.add('dark')
  } else if (darkMode.value === 'light') {
    root.classList.remove('dark')
  } else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
  }
}

function loadSidebarCollapsed(): boolean {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === '1'
}

function saveSidebarCollapsed(value: boolean): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, value ? '1' : '0')
}

function loadAccountsSectionCollapsed(): boolean {
  if (typeof window === 'undefined') return true
  const value = window.localStorage.getItem(ACCOUNTS_SECTION_COLLAPSED_STORAGE_KEY)
  if (value === null) return true
  return value === '1'
}

function toggleAccountsSectionCollapsed(): void {
  isAccountsSectionCollapsed.value = !isAccountsSectionCollapsed.value
  if (typeof window === 'undefined') return
  window.localStorage.setItem(
    ACCOUNTS_SECTION_COLLAPSED_STORAGE_KEY,
    isAccountsSectionCollapsed.value ? '1' : '0',
  )
}

function normalizeMessageType(rawType: string | undefined, role: string): string {
  const normalized = (rawType ?? '').trim()
  if (normalized.length > 0) {
    return normalized
  }
  return role.trim() || 'message'
}

function onSelectCollaborationMode(mode: 'default' | 'plan'): void {
  setSelectedCollaborationMode(mode)
}

async function loadOpenScienceSurfaces(): Promise<void> {
  isLoadingOpenScienceSurfaces.value = true
  openScienceSurfaceError.value = ''
  try {
    const surfaces = await getOpenScienceSurfaces()
    openScienceSurfaces.value = surfaces
    if (!selectedHomeProjectId.value && surfaces.runningProjects.length > 0) {
      selectedHomeProjectId.value = ''
    }
    if (!activeSummaryProjectId.value && surfaces.runningProjectDocs.length > 0) {
      activeSummaryProjectId.value = surfaces.runningProjectDocs[0].id
    }
    if (!activePastProjectId.value && surfaces.pastProjects.length > 0) {
      activePastProjectId.value = surfaces.pastProjects[0].id
    }
    if (!activeDailySummaryId.value && surfaces.dailySummaries.length > 0) {
      activeDailySummaryId.value = surfaces.dailySummaries[0].id
    }
  } catch (error) {
    openScienceSurfaceError.value = error instanceof Error ? error.message : 'Failed to load lab summaries.'
  } finally {
    isLoadingOpenScienceSurfaces.value = false
  }
}

function escapeLabHtml(value: string): string {
  return value
    .replace(/&/gu, '&amp;')
    .replace(/</gu, '&lt;')
    .replace(/>/gu, '&gt;')
    .replace(/"/gu, '&quot;')
    .replace(/'/gu, '&#39;')
}

function normalizeLabMarkdownImageUrl(rawUrl: string): string {
  const url = rawUrl.trim()
  if (url.startsWith('file://')) return `/codex-local-image?path=${encodeURIComponent(url.replace(/^file:\/\//u, ''))}`
  if (url.startsWith('/Volumes/') || url.startsWith('/Users/')) return `/codex-local-image?path=${encodeURIComponent(url)}`
  if (/^https?:\/\//u.test(url) || url.startsWith('/')) return url
  return url
}

function normalizeLabMarkdownLinkUrl(rawUrl: string): string {
  const url = rawUrl.trim()
  if (/^https?:\/\//u.test(url) || url.startsWith('#') || url.startsWith('/')) return url
  return '#'
}

function createLabPlaceholder(kind: 'CODE' | 'MATH', index: number): string {
  return `@@OPENSCIENCE_${kind}_${String(index)}@@`
}

function restoreLabPlaceholders(text: string, kind: 'CODE' | 'MATH', placeholders: string[]): string {
  let restored = text
  placeholders.forEach((html, index) => {
    restored = restored.split(createLabPlaceholder(kind, index)).join(html)
  })
  return restored
}

function renderLabInlineMarkdown(value: string): string {
  const codePlaceholders: string[] = []
  let text = value.replace(/`([^`]+)`/gu, (_match, code: string) => {
    const token = createLabPlaceholder('CODE', codePlaceholders.length)
    codePlaceholders.push(`<code>${escapeLabHtml(code)}</code>`)
    return token
  })

  const mathPlaceholders: string[] = []
  const mathSegments = splitTextByMathSegments(text)
  if (mathSegments.some((segment) => segment.kind === 'math')) {
    text = mathSegments
      .map((segment) => {
        if (segment.kind === 'text') return segment.value
        const token = createLabPlaceholder('MATH', mathPlaceholders.length)
        mathPlaceholders.push(renderMathToHtml(segment.value, segment.displayMode))
        return token
      })
      .join('')
  }

  text = escapeLabHtml(text)
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/gu, (_match, alt: string, url: string) => (
    `<img class="lab-markdown-image" src="${escapeLabHtml(normalizeLabMarkdownImageUrl(url))}" alt="${escapeLabHtml(alt)}" loading="lazy">`
  ))
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/gu, (_match, label: string, url: string) => {
    const normalizedUrl = normalizeLabMarkdownLinkUrl(url)
    const safeUrl = escapeLabHtml(normalizedUrl)
    const target = /^https?:\/\//u.test(normalizedUrl) ? ' target="_blank" rel="noreferrer"' : ''
    return `<a href="${safeUrl}"${target}>${escapeLabHtml(label)}</a>`
  })
  text = text.replace(/\*\*([^*]+)\*\*/gu, '<strong>$1</strong>')
  text = restoreLabPlaceholders(text, 'CODE', codePlaceholders)
  return restoreLabPlaceholders(text, 'MATH', mathPlaceholders)
}

function renderLabMarkdown(markdown: string): string {
  const lines = markdown.replace(/\r/gu, '').split('\n')
  const html: string[] = []
  let inList = false
  let inCode = false
  let codeLines: string[] = []

  const closeList = () => {
    if (!inList) return
    html.push('</ul>')
    inList = false
  }

  for (const line of lines) {
    const codeFence = line.match(/^```([A-Za-z0-9_-]*)\s*$/u)
    if (codeFence) {
      if (inCode) {
        html.push(`<pre><code>${escapeLabHtml(codeLines.join('\n'))}</code></pre>`)
        codeLines = []
        inCode = false
      } else {
        closeList()
        inCode = true
      }
      continue
    }

    if (inCode) {
      codeLines.push(line)
      continue
    }

    if (!line.trim()) {
      closeList()
      continue
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/u)
    if (heading) {
      closeList()
      const level = heading[1]?.length ?? 2
      html.push(`<h${level}>${renderLabInlineMarkdown(heading[2] ?? '')}</h${level}>`)
      continue
    }

    const bullet = line.match(/^\s*[-*]\s+(.+)$/u)
    if (bullet) {
      if (!inList) {
        html.push('<ul>')
        inList = true
      }
      html.push(`<li>${renderLabInlineMarkdown(bullet[1] ?? '')}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${renderLabInlineMarkdown(line)}</p>`)
  }

  closeList()
  if (inCode) {
    html.push(`<pre><code>${escapeLabHtml(codeLines.join('\n'))}</code></pre>`)
  }
  return html.join('')
}

async function initialize(): Promise<void> {
  await router.isReady()

  if (route.name === 'thread' && routeThreadId.value) {
    primeSelectedThread(routeThreadId.value)
  }

  startPolling()
  await refreshAll({
    includeSelectedThreadMessages: true,
  })
  void loadAccountsState({ silent: true })
  hasInitialized.value = true
  await syncThreadSelectionWithRoute()
}

async function syncThreadSelectionWithRoute(): Promise<void> {
  if (isRouteSyncInProgress.value) {
    hasPendingRouteSync = true
    return
  }
  isRouteSyncInProgress.value = true

  try {
    do {
      hasPendingRouteSync = false

      if (route.name === 'home' || route.name === 'skills') {
        if (selectedThreadId.value !== '') {
          await selectThread('')
        }
        continue
      }

      if (route.name === 'thread') {
        const threadId = routeThreadId.value
        if (!threadId) continue

        if (!knownThreadIdSet.value.has(threadId)) {
          await router.replace({ name: 'home' })
          continue
        }

        if (selectedThreadId.value !== threadId) {
          await selectThread(threadId)
        } else {
          void ensureThreadMessagesLoaded(threadId, { silent: true })
        }
      }
    } while (hasPendingRouteSync)

  } finally {
    isRouteSyncInProgress.value = false
  }
}

watch(
  () =>
    [
      route.name,
      routeThreadId.value,
      isLoadingThreads.value,
      knownThreadIdSet.value.has(routeThreadId.value),
      selectedThreadId.value,
    ] as const,
  async () => {
    if (!hasInitialized.value) return
    await syncThreadSelectionWithRoute()
  },
)

watch(
  () => selectedThreadId.value,
  async (threadId) => {
    if (!hasInitialized.value) return
    if (isRouteSyncInProgress.value) return
    if (isHomeRoute.value || isSkillsRoute.value) return

    if (!threadId) {
      if (route.name !== 'home') {
        await router.replace({ name: 'home' })
      }
      return
    }

    if (route.name === 'thread' && routeThreadId.value === threadId) return
    await router.replace({ name: 'thread', params: { threadId } })
  },
)

watch(
  () => [hasInitialized.value, route.name, selectedThreadId.value] as const,
  ([ready, routeName, threadId]) => {
    if (!ready) return
    if (routeName !== 'thread') return
    if (!threadId) return
    void ensureThreadMessagesLoaded(threadId, { silent: true })
  },
)

watch(
  pageTitle,
  (value) => {
    if (typeof document === 'undefined') return
    document.title = value
  },
  { immediate: true },
)


watch(
  isMobile,
  (mobile) => {
    if (mobile && !isSidebarCollapsed.value) {
      setSidebarCollapsed(true)
    }
  },
  { immediate: true },
)

async function submitFirstMessageForNewThread(
  text: string,
  imageUrls: string[] = [],
  skills: Array<{ name: string; path: string }> = [],
  fileAttachments: Array<{ label: string; path: string; fsPath: string }> = [],
): Promise<void> {
  try {
    const targetCwd = newThreadCwd.value.trim() || DEFAULT_OPENSCIENCE_WORKSPACE
    const threadId = await sendMessageToNewThread(text, targetCwd, imageUrls, skills, fileAttachments, selectedHomeProjectId.value)
    if (!threadId) return
    await router.replace({ name: 'thread', params: { threadId } })
    scheduleMobileConversationJumpToLatest()
  } catch {
    // Error is already reflected in state.
  }
}
</script>

<style scoped>
@reference "tailwindcss";

.sidebar-root {
  @apply h-full flex flex-col select-none;
  background:
    linear-gradient(180deg, rgba(12, 148, 136, 0.08), transparent 18rem),
    linear-gradient(90deg, rgba(15, 23, 42, 0.05), transparent 55%),
    rgb(244 246 245);
}

.sidebar-root input,
.sidebar-root textarea {
  @apply select-text;
}

.sidebar-scrollable {
  @apply flex-1 min-h-0 overflow-y-auto py-4 px-2 flex flex-col gap-2;
}

.content-root {
  @apply h-full min-h-0 min-w-0 w-full flex flex-col overflow-y-hidden overflow-x-hidden;
  background:
    radial-gradient(circle at 20% 12%, rgba(20, 184, 166, 0.12), transparent 23rem),
    radial-gradient(circle at 85% 18%, rgba(225, 29, 72, 0.08), transparent 19rem),
    linear-gradient(180deg, rgb(248 250 249), rgb(255 255 255) 35%);
}

.sidebar-thread-controls-host {
  @apply mt-1 -translate-y-px px-2 pb-1;
}

.sidebar-search-toggle {
  @apply h-6.75 w-6.75 rounded-md border border-transparent bg-transparent text-zinc-600 flex items-center justify-center transition hover:border-zinc-200 hover:bg-zinc-50;
}

.sidebar-search-toggle[aria-pressed='true'] {
  @apply border-zinc-300 bg-zinc-100 text-zinc-700;
}

.sidebar-search-toggle-icon {
  @apply w-4 h-4;
}

.sidebar-search-bar {
  @apply flex items-center gap-1.5 mx-2 px-2 py-1 rounded-md border border-zinc-200 bg-white transition-colors focus-within:border-zinc-400;
}

.sidebar-search-bar-icon {
  @apply w-3.5 h-3.5 text-zinc-400 shrink-0;
}

.sidebar-search-input {
  @apply flex-1 min-w-0 bg-transparent text-sm text-zinc-800 placeholder-zinc-400 outline-none border-none p-0;
}

.sidebar-search-clear {
  @apply w-4 h-4 rounded text-zinc-400 flex items-center justify-center transition hover:text-zinc-600;
}

.sidebar-search-clear-icon {
  @apply w-3.5 h-3.5;
}

.sidebar-skills-link {
  @apply mx-2 flex items-center rounded-lg border border-transparent bg-transparent px-2 py-1.5 text-sm text-zinc-700 transition hover:border-teal-200 hover:bg-teal-50 hover:text-zinc-950 cursor-pointer;
}

.sidebar-skills-link.is-active {
  @apply border-teal-200 bg-teal-50 text-zinc-950 font-medium;
}

.sidebar-thread-controls-header-host {
  @apply ml-1;
}

.content-body {
  @apply flex-1 min-h-0 min-w-0 w-full flex flex-col gap-2 sm:gap-3 pt-1 pb-2 sm:pb-4 overflow-x-hidden;
}



.content-error {
  @apply m-0 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700;
}

.content-grid {
  @apply flex-1 min-h-0 flex flex-col gap-3;
}

.content-grid-home {
  @apply overflow-y-auto;
  scrollbar-gutter: stable;
}

.content-thread {
  @apply flex-1 min-h-0;
}

.composer-with-queue {
  @apply w-full shrink-0 px-2 sm:px-6;
}

.new-thread-empty {
  @apply flex-1 min-h-0 flex flex-col items-center justify-start gap-1.5 px-3 py-2 sm:px-6 text-center;
}

.new-thread-kicker {
  @apply m-0 text-xs font-semibold uppercase text-teal-700;
  letter-spacing: 0;
}

.new-thread-hero {
  @apply m-0 text-3xl sm:text-[2.5rem] font-semibold leading-[1.05] text-zinc-950;
}

.new-thread-subtitle {
  @apply m-0 max-w-2xl text-xs leading-5 text-zinc-600;
}

.lab-home-panel {
  @apply mt-2 flex w-full max-w-5xl flex-1 min-h-0 flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white/92 text-left shadow-sm;
}

.lab-panel-heading {
  @apply flex flex-col gap-2 border-b border-zinc-200 px-3 py-2 sm:flex-row sm:items-center sm:justify-between;
}

.lab-panel-title {
  @apply m-0 text-xs font-semibold text-zinc-950;
}

.lab-panel-description {
  @apply m-0 mt-0.5 text-[11px] leading-4 text-zinc-500;
}

.lab-panel-open {
  @apply inline-flex h-7 shrink-0 items-center justify-center rounded-md border border-zinc-300 bg-white px-2.5 text-xs font-medium text-zinc-700 transition hover:border-zinc-400 hover:bg-zinc-50 disabled:cursor-default disabled:opacity-50;
}

.lab-home-controls {
  @apply flex flex-col gap-1.5 border-b border-zinc-200 px-3 py-2 sm:flex-row sm:items-center sm:justify-between;
}

.lab-home-control-copy {
  @apply min-w-0;
}

.lab-project-select-label {
  @apply block text-[11px] font-semibold uppercase text-zinc-500;
  letter-spacing: 0;
}

.lab-project-select-help {
  @apply m-0 mt-0.5 text-[11px] text-zinc-500;
}

.lab-project-select-wrap {
  @apply min-w-0;
}

.lab-project-select {
  @apply h-8 w-full min-w-0 rounded-md border border-zinc-300 bg-white px-2 text-xs text-zinc-900 outline-none transition focus:border-teal-500 sm:min-w-64;
}

.lab-tabs-row {
  @apply flex flex-col gap-1.5 border-b border-zinc-200 px-3 py-1.5 sm:flex-row sm:items-center;
}

.lab-tabs-label {
  @apply px-1 text-[11px] font-semibold uppercase text-zinc-500;
  letter-spacing: 0;
}

.lab-home-tabs {
  @apply flex gap-1;
}

.lab-home-tab {
  @apply rounded-md border border-transparent bg-transparent px-2.5 py-1 text-xs font-medium text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950;
}

.lab-home-tab.is-active {
  @apply border-teal-200 bg-teal-50 text-teal-800;
}

.lab-home-summary {
  @apply grid flex-1 min-h-0 grid-cols-1 overflow-hidden sm:grid-cols-[15rem_minmax(0,1fr)];
}

.lab-home-summary.is-single-document {
  @apply grid-cols-1;
}

.lab-summary-list {
  @apply flex max-h-40 min-h-0 flex-col gap-1 overflow-y-auto border-b border-zinc-200 p-2 sm:max-h-none sm:border-b-0 sm:border-r;
}

.lab-summary-list-item {
  @apply flex flex-col items-start rounded-md border border-transparent bg-transparent px-2 py-2 text-left text-sm text-zinc-700 transition hover:bg-zinc-100;
}

.lab-summary-list-item.is-active {
  @apply border-teal-200 bg-teal-50 text-zinc-950;
}

.lab-summary-list-item small {
  @apply mt-0.5 text-xs text-zinc-500;
}

.lab-summary-document {
  @apply h-full min-h-0 overflow-y-auto px-5 py-4 pb-12;
}

.lab-summary-history {
  @apply mb-3 flex flex-col gap-1 rounded-md border border-teal-900/40 bg-zinc-950 px-3 py-2 sm:flex-row sm:items-center sm:justify-between;
}

.lab-summary-history-label {
  @apply text-xs font-semibold uppercase text-teal-200;
  letter-spacing: 0;
}

.lab-summary-history-select {
  @apply h-8 min-w-0 rounded-md border border-teal-800 bg-zinc-900 px-2 text-sm text-zinc-100 outline-none transition focus:border-teal-300 sm:w-56;
}

.lab-summary-document-header {
  @apply mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b border-zinc-200 pb-2;
}

.lab-summary-document-title {
  @apply min-w-0 flex-1;
}

.lab-summary-document-header span {
  @apply text-sm font-semibold text-zinc-950;
}

.lab-summary-document-path {
  @apply mt-0.5 block max-w-full truncate font-mono text-[11px] text-zinc-500;
}

.lab-summary-document-header small {
  @apply text-xs text-zinc-500;
}

.lab-summary-empty {
  @apply text-sm leading-6 text-zinc-500;
}

.lab-markdown {
  @apply max-w-none text-sm leading-6 text-zinc-700;
}

.lab-markdown :deep(h1),
.lab-markdown :deep(h2),
.lab-markdown :deep(h3),
.lab-markdown :deep(h4) {
  @apply mb-2 mt-4 font-semibold leading-tight text-zinc-950;
}

.lab-markdown :deep(h1) {
  @apply mt-0 text-2xl;
}

.lab-markdown :deep(h2) {
  @apply text-xl;
}

.lab-markdown :deep(h3) {
  @apply text-base;
}

.lab-markdown :deep(p) {
  @apply my-2;
}

.lab-markdown :deep(ul) {
  @apply my-2 list-disc pl-5;
}

.lab-markdown :deep(li) {
  @apply my-1;
}

.lab-markdown :deep(a) {
  @apply text-teal-700 underline underline-offset-2;
}

.lab-markdown :deep(code) {
  @apply rounded border border-zinc-200 bg-zinc-100 px-1 py-0.5 font-mono text-[0.9em] text-zinc-900;
}

.lab-markdown :deep(pre) {
  @apply my-3 overflow-x-auto rounded-lg border border-zinc-200 bg-zinc-950 px-3 py-2 text-zinc-100;
}

.lab-markdown :deep(pre code) {
  @apply border-0 bg-transparent p-0 text-zinc-100;
}

.lab-markdown :deep(.lab-markdown-image) {
  @apply my-3 max-h-80 max-w-full rounded-md border border-zinc-200 object-contain;
}

.lab-markdown :deep(.katex) {
  font-size: 1.02em;
}

.lab-markdown :deep(.katex-display) {
  @apply my-3 overflow-x-auto overflow-y-hidden py-1;
}

:global(:root.dark) .lab-markdown {
  @apply text-zinc-200;
}

:global(:root.dark) .lab-markdown :deep(h1),
:global(:root.dark) .lab-markdown :deep(h2),
:global(:root.dark) .lab-markdown :deep(h3),
:global(:root.dark) .lab-markdown :deep(h4) {
  @apply text-zinc-50;
}

:global(:root.dark) .lab-markdown :deep(.katex),
:global(:root.dark) .lab-markdown :deep(.katex *) {
  color: rgb(244 244 245);
}

.new-thread-project-context {
  @apply mt-2 rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-xs text-teal-800;
}

.lab-reader-backdrop {
  @apply fixed inset-0 z-50 flex items-stretch justify-center bg-black/45 p-3 sm:p-6;
}

.lab-reader {
  @apply flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-2xl;
}

.lab-reader-header {
  @apply flex shrink-0 items-start justify-between gap-4 border-b border-zinc-200 px-5 py-4;
}

.lab-reader-kicker {
  @apply m-0 text-xs font-semibold uppercase text-teal-700;
  letter-spacing: 0;
}

.lab-reader-header h2 {
  @apply m-0 mt-1 text-xl font-semibold text-zinc-950;
}

.lab-reader-source {
  @apply m-0 mt-1 max-w-[72vw] truncate font-mono text-xs text-zinc-500;
}

.lab-reader-close {
  @apply inline-flex h-8 shrink-0 items-center justify-center rounded-md border border-zinc-300 bg-white px-3 text-sm font-medium text-zinc-700 transition hover:border-zinc-400 hover:bg-zinc-50;
}

.lab-reader-body {
  @apply min-h-0 flex-1 overflow-y-auto px-5 py-4 pb-10 sm:px-8;
}

@media (max-width: 640px) {
  .new-thread-empty {
    @apply justify-start py-4;
  }

  .lab-home-panel {
    @apply mt-3;
  }

  .lab-home-tabs {
    @apply overflow-x-auto;
  }

  .lab-home-tab {
    @apply shrink-0;
  }

  .lab-home-summary {
    min-height: 0;
  }
}

@media (max-height: 820px) {
  .new-thread-empty {
    @apply gap-1.5 py-2;
  }

  .new-thread-subtitle {
    @apply text-xs leading-5;
  }

  .lab-home-panel {
    @apply mt-3;
  }

  .lab-panel-heading,
  .lab-home-controls {
    @apply px-4 py-2.5;
  }

  .lab-tabs-row {
    @apply py-1.5;
  }

  .lab-home-summary {
    min-height: 0;
  }
}

.new-thread-folder-dropdown {
  @apply text-2xl sm:text-[2.5rem] text-zinc-500;
}

.new-thread-folder-dropdown :deep(.composer-dropdown-trigger) {
  @apply h-auto p-0 text-2xl sm:text-[2.5rem] leading-[1.05];
}

.new-thread-folder-dropdown :deep(.composer-dropdown-value) {
  @apply leading-[1.05];
}

.new-thread-folder-dropdown :deep(.composer-dropdown-chevron) {
  @apply h-4 w-4 sm:h-5 sm:w-5 mt-0;
}

.new-thread-folder-actions {
  @apply mt-3 flex w-full max-w-3xl flex-wrap items-center justify-center gap-2;
}

.new-thread-folder-action {
  @apply inline-flex h-9 items-center justify-center rounded-full border border-zinc-200 bg-white px-4 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-default disabled:opacity-60;
}

.new-thread-folder-action-primary {
  @apply border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800;
}

.new-thread-open-folder {
  @apply mt-3 flex w-full max-w-3xl flex-col gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-4 text-left shadow-sm;
}

.new-thread-open-folder-header {
  @apply flex items-center justify-between gap-3;
}

.new-thread-open-folder-title {
  @apply m-0 text-sm font-semibold text-zinc-900;
}

.new-thread-open-folder-close {
  @apply border-0 bg-transparent p-0 text-sm text-zinc-500 transition hover:text-zinc-800;
}

.new-thread-open-folder-label {
  @apply m-0 text-xs font-medium uppercase tracking-wide text-zinc-500;
}

.new-thread-open-folder-current {
  @apply flex items-start gap-2;
}

.new-thread-open-folder-path {
  @apply m-0 min-w-0 flex-1 rounded-xl bg-zinc-100 px-3 py-2 font-mono text-xs text-zinc-700 break-all;
}

.new-thread-open-folder-actions {
  @apply flex flex-wrap items-center gap-2;
}

.new-thread-open-folder-toggle {
  @apply inline-flex items-center gap-2 text-sm text-zinc-600;
}

.new-thread-open-folder-toggle-input {
  @apply relative h-4 w-4 shrink-0 appearance-none rounded-[4px] border border-zinc-300 bg-white outline-none transition;
}

.new-thread-open-folder-toggle-input:focus-visible {
  box-shadow: 0 0 0 3px rgb(228 228 231);
}

.new-thread-open-folder-toggle-input:checked {
  border-color: rgb(24 24 27);
  background-color: rgb(255 255 255);
}

.new-thread-open-folder-toggle-input::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border-right: 2px solid rgb(24 24 27);
  border-bottom: 2px solid rgb(24 24 27);
  transform: rotate(45deg);
  opacity: 0;
}

.new-thread-open-folder-toggle-input:checked::after {
  opacity: 1;
}

.new-thread-open-folder-filter {
  @apply w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-zinc-400;
}

.new-thread-open-folder-create {
  @apply flex flex-col gap-2;
}

.new-thread-open-folder-create-composer {
  @apply flex items-center gap-2;
}

.new-thread-open-folder-create-input {
  @apply w-full min-w-0 flex-1 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-zinc-400;
}

.new-thread-open-folder-create-submit {
  @apply shrink-0;
}

.new-thread-folder-action[aria-pressed='true'] {
  @apply border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800;
}

.new-thread-open-folder-status {
  @apply m-0 rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-600;
}

.new-thread-open-folder-error {
  @apply m-0 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700;
}

.new-thread-open-folder-error-actions {
  @apply flex flex-wrap items-start gap-2;
}

.new-thread-open-folder-list {
  @apply m-0 flex max-h-72 list-none flex-col gap-1 overflow-y-auto p-0 pr-3;
  scrollbar-gutter: stable;
  scrollbar-color: rgb(161 161 170) rgb(244 244 245);
  scrollbar-width: thin;
}

.new-thread-open-folder-list::-webkit-scrollbar {
  width: 10px;
}

.new-thread-open-folder-list::-webkit-scrollbar-track {
  background: rgb(244 244 245);
  border-radius: 9999px;
}

.new-thread-open-folder-list::-webkit-scrollbar-thumb {
  background: rgb(161 161 170);
  border-radius: 9999px;
  border: 2px solid rgb(244 244 245);
}

.new-thread-open-folder-list::-webkit-scrollbar-thumb:hover {
  background: rgb(113 113 122);
}

.new-thread-open-folder-item {
  @apply grid grid-cols-[minmax(0,1fr)_auto] items-center gap-1;
}

.new-thread-open-folder-item-main {
  @apply min-w-0 truncate rounded-xl border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-left text-sm font-medium leading-5 text-zinc-900 transition hover:border-zinc-300 hover:bg-zinc-100;
}

.new-thread-open-folder-item-main:disabled,
.new-thread-open-folder-item-open:disabled {
  @apply cursor-default opacity-60;
}

.new-thread-open-folder-item-name {
  @apply block truncate;
}

.new-thread-open-folder-item-open {
  @apply inline-flex h-7 items-center justify-center rounded-xl border border-zinc-200 bg-white px-2.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50;
}

.new-thread-runtime-dropdown {
  @apply mt-3;
}

.new-thread-branch-select {
  @apply mt-3 w-full max-w-3xl;
}

.new-thread-branch-select-label {
  @apply m-0 mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500;
}

.new-thread-branch-dropdown :deep(.composer-dropdown-trigger) {
  @apply h-9 rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-700;
}

.new-thread-branch-select-help {
  @apply mt-1 mb-0 text-xs text-zinc-500;
}

.new-thread-trending {
  @apply mt-4 w-full max-w-3xl;
}

.new-thread-trending-header {
  @apply mb-2 flex items-center justify-between gap-2;
}

.new-thread-trending-title {
  @apply m-0 text-xs font-medium uppercase tracking-wide text-zinc-500;
}

.new-thread-trending-scope-dropdown {
  @apply min-w-40;
}

.new-thread-trending-scope-dropdown :deep(.composer-dropdown-trigger) {
  @apply h-8 rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700;
}

.new-thread-trending-empty {
  @apply m-0 text-sm text-zinc-500;
}

.new-thread-trending-list {
  @apply grid grid-cols-2 sm:grid-cols-3 gap-2;
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.new-thread-trending-tip {
  @apply flex cursor-pointer flex-col items-start gap-1 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-left transition hover:border-zinc-300 hover:bg-zinc-50;
  container-type: inline-size;
}

.new-thread-trending-tip-name {
  @apply w-full truncate text-sm font-medium text-zinc-900;
}

.new-thread-trending-tip-name-owner {
  @apply inline;
}

.new-thread-trending-tip-name-slash {
  @apply inline;
}

.new-thread-trending-tip-name-repo {
  @apply inline;
}

@container (max-width: 220px) {
  .new-thread-trending-tip-name-owner,
  .new-thread-trending-tip-name-slash {
    display: none;
  }
}

.new-thread-trending-tip-meta {
  @apply text-xs text-zinc-500;
}

.new-thread-trending-tip-description {
  @apply line-clamp-2 text-xs text-zinc-600;
}

.worktree-init-status {
  @apply mt-3 flex w-full max-w-xl flex-col gap-1 rounded-xl border px-3 py-2 text-sm;
}

.worktree-init-status.is-running {
  @apply border-zinc-300 bg-zinc-50 text-zinc-700;
}

.worktree-init-status.is-error {
  @apply border-rose-300 bg-rose-50 text-rose-800;
}

.worktree-init-status-title {
  @apply font-medium;
}

.worktree-init-status-message {
  @apply break-all;
}

.sidebar-settings-area {
  @apply shrink-0 bg-slate-100 pt-2 px-2 pb-2 border-t border-zinc-200;
}

.sidebar-settings-button {
  @apply flex items-center gap-2 w-full rounded-lg border-0 bg-transparent px-2 py-2 text-sm text-zinc-600 transition hover:bg-zinc-200 hover:text-zinc-900 cursor-pointer;
}

.sidebar-settings-button-version {
  @apply ml-auto min-w-0 truncate text-right text-xs;
}

.sidebar-settings-icon {
  @apply w-4.5 h-4.5;
}

.sidebar-settings-panel {
  @apply mb-1 rounded-lg border border-zinc-200 bg-white overflow-hidden;
}

.sidebar-settings-row {
  @apply flex items-center justify-between w-full px-3 py-2.5 text-sm text-zinc-700 border-0 bg-transparent transition hover:bg-zinc-50 cursor-pointer;
}

.sidebar-settings-row--select {
  @apply cursor-default items-center gap-2;
}

.sidebar-settings-language-dropdown {
  @apply min-w-0 max-w-52;
}

.sidebar-settings-language-dropdown :deep(.composer-dropdown-trigger) {
  @apply h-auto rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700;
}

.sidebar-settings-language-dropdown :deep(.composer-dropdown-value) {
  @apply max-w-32;
}

.sidebar-settings-row + .sidebar-settings-row {
  @apply border-t border-zinc-100;
}

.sidebar-settings-account-section {
  @apply border-t border-zinc-100 bg-zinc-50/60 px-3 py-3;
}

.sidebar-settings-account-header {
  @apply mb-2 flex items-center justify-between gap-2;
}

.sidebar-settings-account-header-main {
  @apply flex items-center gap-2;
}

.sidebar-settings-account-collapse {
  @apply inline-flex h-5 w-5 items-center justify-center rounded border border-zinc-200 bg-white text-zinc-600 transition hover:bg-zinc-100;
}

.sidebar-settings-account-collapse-icon {
  @apply text-[11px] leading-none;
}

.sidebar-settings-account-title {
  @apply text-sm font-medium text-zinc-800;
}

.sidebar-settings-account-count {
  @apply rounded bg-zinc-200 px-1.5 py-0.5 text-[11px] text-zinc-600;
}

.sidebar-settings-account-error {
  @apply mb-2 rounded-md bg-rose-50 px-2 py-1.5 text-xs text-rose-700;
}

.sidebar-settings-account-refresh {
  @apply shrink-0 rounded-full border border-zinc-200 bg-white px-2.5 py-1 text-xs text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-default disabled:opacity-60;
}

.sidebar-settings-account-empty {
  @apply text-xs text-zinc-500;
}

.sidebar-settings-account-list {
  @apply flex max-h-56 flex-col gap-2 overflow-y-auto;
}

.sidebar-settings-account-item {
  @apply flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-2.5 py-2;
}

.sidebar-settings-account-item.is-active {
  @apply border-emerald-200 bg-emerald-50;
}

.sidebar-settings-account-item.is-unavailable {
  @apply border-rose-200 bg-rose-50;
}

.sidebar-settings-account-main {
  @apply min-w-0 flex-1;
}

.sidebar-settings-account-actions {
  @apply flex w-24 shrink-0 flex-col items-end gap-1.5;
}

.sidebar-settings-account-email {
  @apply truncate text-sm text-zinc-800;
}

.sidebar-settings-account-meta {
  @apply truncate text-[11px] text-zinc-500;
}

.sidebar-settings-account-quota {
  @apply truncate text-[11px] text-zinc-600;
}

.sidebar-settings-account-id {
  @apply mt-1 inline-flex max-w-full rounded-full bg-zinc-100 px-2 py-0.5 font-mono text-[11px] text-zinc-700;
}

.sidebar-settings-account-item.is-active .sidebar-settings-account-id {
  @apply bg-emerald-100 text-emerald-800;
}

.sidebar-settings-account-item.is-unavailable .sidebar-settings-account-id {
  @apply bg-rose-100 text-rose-800;
}

.sidebar-settings-account-switch {
  @apply min-w-[4.75rem] shrink-0 rounded-full border border-zinc-200 bg-white px-2.5 py-1 text-center text-xs text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-default disabled:opacity-60;
}

.sidebar-settings-account-remove {
  @apply invisible shrink-0 rounded-full border border-amber-200 bg-white px-2 py-0.5 text-[10px] leading-4 text-zinc-500 opacity-0 pointer-events-none transition-colors hover:bg-amber-50 disabled:cursor-default disabled:opacity-60;
}

.sidebar-settings-account-remove.is-visible {
  @apply visible opacity-100 pointer-events-auto;
}

.sidebar-settings-account-remove.is-confirming {
  @apply border-amber-300 bg-amber-50 text-amber-700 font-medium;
}

.sidebar-settings-label {
  @apply text-left;
}

.sidebar-settings-value {
  @apply text-xs text-zinc-500 bg-zinc-100 rounded px-1.5 py-0.5;
}


.sidebar-settings-toggle {
  @apply relative w-9 h-5 rounded-full bg-zinc-300 transition-colors shrink-0;
}

.sidebar-settings-toggle::after {
  content: '';
  @apply absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm;
}

.sidebar-settings-toggle.is-on {
  @apply bg-zinc-800;
}

.sidebar-settings-toggle.is-on::after {
  transform: translateX(16px);
}

.settings-panel-enter-active,
.settings-panel-leave-active {
  transition: all 150ms ease;
}

.settings-panel-enter-from,
.settings-panel-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.sidebar-settings-context-row {
  @apply cursor-default;
}

.sidebar-settings-context-value {
  @apply text-xs font-semibold text-zinc-700 text-right;
}

.sidebar-settings-context-value[data-state='ok'] {
  @apply text-emerald-700;
}

.sidebar-settings-context-value[data-state='warning'] {
  @apply text-amber-700;
}

.sidebar-settings-context-value[data-state='danger'] {
  @apply text-rose-700;
}

.sidebar-settings-context-meta {
  @apply block text-[11px] font-normal text-zinc-500;
}

.sidebar-settings-rate-limits {
  @apply border-t border-zinc-200 px-2 pt-2;
}

.sidebar-settings-build-label {
  @apply border-t border-zinc-100 px-3 py-2 text-[11px] text-zinc-500;
}

</style>
