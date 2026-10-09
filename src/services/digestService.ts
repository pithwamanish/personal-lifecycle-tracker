import { DailyDigestConfig, DailyDigestEmail, LifecycleItem } from './types';
import { formatDisplayDate, getRelativeDueDateLabel, getTodayDateString } from './dateUtils';

export function buildDailyDigestEmail(params: {
  recipientEmail: string;
  recipientName: string;
  config: DailyDigestConfig;
  overdueItems: LifecycleItem[];
  upcomingItems: LifecycleItem[];
}): DailyDigestEmail {
  const { recipientEmail, recipientName, config, overdueItems, upcomingItems } = params;
  const todayStr = getTodayDateString();

  const totalCount = overdueItems.length + upcomingItems.length;
  const subject =
    totalCount === 0
      ? `[Lifecycle Tracker] All clear for today (${todayStr})`
      : overdueItems.length > 0
      ? `[Action Required] ${overdueItems.length} overdue & ${upcomingItems.length} upcoming lifecycle items`
      : `[Upcoming Actions] ${upcomingItems.length} upcoming lifecycle items`;

  // Text content
  const textLines: string[] = [
    `PERSONAL LIFECYCLE TRACKER - DAILY DIGEST`,
    `Generated for: ${recipientName} (${recipientEmail})`,
    `Date: ${todayStr} | Scheduled delivery: ${config.deliveryTime} (${config.timeZone})`,
    `--------------------------------------------------`,
    ``,
  ];

  if (overdueItems.length > 0) {
    textLines.push(`🔴 OVERDUE ITEMS (${overdueItems.length}):`);
    overdueItems.forEach((item, idx) => {
      const rel = getRelativeDueDateLabel(item.dueDate, item.status, todayStr);
      const groupInfo = item.groupName ? ` [Group: ${item.groupName}]` : ' [Personal]';
      textLines.push(`  ${idx + 1}. [${item.lifecycleType.toUpperCase()}] ${item.name}`);
      textLines.push(`     Due: ${formatDisplayDate(item.dueDate)} (${rel})${groupInfo}`);
    });
    textLines.push(``);
  }

  if (upcomingItems.length > 0) {
    textLines.push(`🟡 UPCOMING ITEMS (${upcomingItems.length}):`);
    upcomingItems.forEach((item, idx) => {
      const rel = getRelativeDueDateLabel(item.dueDate, item.status, todayStr);
      const groupInfo = item.groupName ? ` [Group: ${item.groupName}]` : ' [Personal]';
      textLines.push(`  ${idx + 1}. [${item.lifecycleType.toUpperCase()}] ${item.name}`);
      textLines.push(`     Due: ${formatDisplayDate(item.dueDate)} (${rel})${groupInfo}`);
    });
    textLines.push(``);
  }

  if (totalCount === 0) {
    textLines.push(`You have zero overdue or upcoming items scheduled for the next 30 days.`);
    textLines.push(``);
  }

  textLines.push(`--------------------------------------------------`);
  textLines.push(`Delivered automatically by your Daily Digest schedule.`);
  textLines.push(`Note: Reminder channels are always active.`);

  // HTML content
  const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${subject}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }
    .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }
    .header { background: #0f172a; color: #ffffff; padding: 24px; }
    .header h1 { margin: 0 0 6px 0; font-size: 20px; font-weight: 600; letter-spacing: -0.02em; }
    .header p { margin: 0; font-size: 13px; color: #94a3b8; }
    .content { padding: 24px; }
    .badge { display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 600; text-transform: uppercase; border-radius: 4px; }
    .badge-overdue { background: #fee2e2; color: #991b1b; }
    .badge-upcoming { background: #fef3c7; color: #92400e; }
    .section-title { font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin: 20px 0 12px 0; color: #475569; }
    .item-card { border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; background: #fafafa; }
    .item-title { font-weight: 600; font-size: 14px; color: #0f172a; }
    .item-meta { font-size: 12px; color: #64748b; margin-top: 4px; }
    .footer { padding: 16px 24px; background: #f1f5f9; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Personal Lifecycle Tracker</h1>
      <p>Daily Digest for ${recipientName} &bull; ${todayStr} &bull; ${config.deliveryTime} (${config.timeZone})</p>
    </div>
    <div class="content">
      ${
        overdueItems.length > 0
          ? `
        <div class="section-title" style="color: #b91c1c;">⚠️ Overdue Items (${overdueItems.length})</div>
        ${overdueItems
          .map(
            (item) => `
          <div class="item-card" style="border-left: 3px solid #ef4444;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="item-title">${item.name}</span>
              <span class="badge badge-overdue">${item.lifecycleType}</span>
            </div>
            <div class="item-meta">
              <strong>Due:</strong> ${formatDisplayDate(item.dueDate)} &bull; ${getRelativeDueDateLabel(item.dueDate, item.status, todayStr)}
              ${item.groupName ? ` &bull; <span>Group: ${item.groupName}</span>` : ' &bull; <span>Personal</span>'}
            </div>
          </div>
        `
          )
          .join('')}
      `
          : ''
      }

      ${
        upcomingItems.length > 0
          ? `
        <div class="section-title" style="color: #b45309;">⏳ Upcoming Actions (${upcomingItems.length})</div>
        ${upcomingItems
          .map(
            (item) => `
          <div class="item-card" style="border-left: 3px solid #f59e0b;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="item-title">${item.name}</span>
              <span class="badge badge-upcoming">${item.lifecycleType}</span>
            </div>
            <div class="item-meta">
              <strong>Due:</strong> ${formatDisplayDate(item.dueDate)} &bull; ${getRelativeDueDateLabel(item.dueDate, item.status, todayStr)}
              ${item.groupName ? ` &bull; <span>Group: ${item.groupName}</span>` : ' &bull; <span>Personal</span>'}
            </div>
          </div>
        `
          )
          .join('')}
      `
          : ''
      }

      ${
        totalCount === 0
          ? `
        <div style="text-align: center; padding: 32px 16px; color: #64748b;">
          <div style="font-size: 24px; margin-bottom: 8px;">✅</div>
          <div style="font-size: 15px; font-weight: 600; color: #0f172a;">All caught up!</div>
          <div style="font-size: 13px;">No overdue or upcoming actions in the next 30 days.</div>
        </div>
      `
          : ''
      }
    </div>
    <div class="footer">
      This is an automated daily digest from Personal Lifecycle Tracker. Reminders and digests are scheduled automatically.
    </div>
  </div>
</body>
</html>
  `.trim();

  return {
    id: `digest_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    recipientEmail,
    recipientName,
    generatedAt: new Date().toISOString(),
    deliveryTime: config.deliveryTime,
    timeZone: config.timeZone,
    subject,
    overdueCount: overdueItems.length,
    upcomingCount: upcomingItems.length,
    overdueItems,
    upcomingItems,
    htmlContent,
    textContent: textLines.join('\n'),
  };
}
