/**
 * 图表渲染组件
 *
 * 支持两种模式：
 * 1. 图片模式：显示MCP生成的图表图片
 * 2. G2模式：使用AntV G2渲染图表
 */

import React, { useEffect, useRef } from 'react';
import { Chart } from '@antv/g2';
import type { Chart as ChartType } from '../../types/api';

interface ChartRendererProps {
  chart: ChartType;
}

export default function ChartRenderer({ chart }: ChartRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  // 检查是否是图片类型
  const isImageType = chart.chart_config.type === 'image' && chart.chart_config.url;

  useEffect(() => {
    // 如果是图片类型，不需要用G2渲染
    if (isImageType) return;

    if (!containerRef.current) return;

    // 创建图表实例
    const chartInstance = new Chart({
      container: containerRef.current,
      autoFit: true,
      height: 300,
    });

    // 应用MCP服务器返回的配置
    try {
      const config = chart.chart_config;

      // 设置数据
      if (config.data) {
        chartInstance.data(config.data);
      }

      // 根据图表类型创建图形
      const chartType = chart.chart_type || config.type;

      switch (chartType) {
        case 'bar':
          chartInstance
            .interval()
            .encode('x', config.xField || 'x')
            .encode('y', config.yField || 'y');
          break;

        case 'line':
          chartInstance
            .line()
            .encode('x', config.xField || 'x')
            .encode('y', config.yField || 'y');
          break;

        case 'pie':
          chartInstance
            .interval()
            .coordinate({ type: 'theta' })
            .encode('y', config.angleField || 'value')
            .encode('color', config.colorField || 'category')
            .legend('color', { position: 'right' });
          break;

        case 'scatter':
          chartInstance
            .point()
            .encode('x', config.xField || 'x')
            .encode('y', config.yField || 'y')
            .encode('size', config.sizeField || 5);
          break;

        default:
          // 尝试直接应用配置
          console.warn(`未知图表类型: ${chartType},尝试直接应用配置`);
      }

      // 渲染图表
      chartInstance.render();

      chartInstanceRef.current = chartInstance;
    } catch (error) {
      console.error('图表渲染失败:', error);
    }

    // 清理
    return () => {
      chartInstanceRef.current?.destroy();
    };
  }, [chart, isImageType]);

  return (
    <div
      style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
        border: '1px solid #e8e9eb',
      }}
    >
      {chart.chart_config.title && (
        <h4
          style={{
            margin: '0 0 16px 0',
            fontSize: '16px',
            fontWeight: 600,
            color: '#1f2329',
          }}
        >
          📊 {chart.chart_config.title}
        </h4>
      )}

      {isImageType ? (
        // 图片模式：直接显示图片
        <div>
          <div
            style={{
              textAlign: 'center',
              backgroundColor: '#f7f8fa',
              borderRadius: '8px',
              padding: '12px',
              overflow: 'hidden',
            }}
          >
            <img
              src={chart.chart_config.url}
              alt={`${chart.chart_type} 图表`}
              style={{
                maxWidth: '100%',
                height: 'auto',
                borderRadius: '6px',
                display: 'block',
                margin: '0 auto',
              }}
              onError={(e) => {
                console.error('图片加载失败:', chart.chart_config.url);
                e.currentTarget.style.display = 'none';
                const parent = e.currentTarget.parentElement;
                if (parent) {
                  parent.innerHTML = `
                    <div style="
                      color: #f54a45;
                      padding: 40px 20px;
                      text-align: center;
                      background-color: #fff1f0;
                      border-radius: 8px;
                      border: 1px dashed #ffccc7;
                    ">
                      <div style="font-size: 32px; margin-bottom: 12px;">❌</div>
                      <div style="font-size: 14px; font-weight: 500;">图片加载失败</div>
                      <div style="font-size: 12px; color: #cf1322; margin-top: 8px;">
                        请检查网络连接或图片地址
                      </div>
                    </div>
                  `;
                }
              }}
            />
          </div>
          <div
            style={{
              fontSize: '13px',
              color: '#8f959e',
              marginTop: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 12px',
              backgroundColor: '#f7f8fa',
              borderRadius: '6px',
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>📈</span>
              <span style={{ fontWeight: 500 }}>
                {chart.chart_type?.replace(/-/g, ' ').toUpperCase()}
              </span>
            </span>
            <span style={{ fontSize: '12px' }}>
              由 {chart.chart_config.tool?.replace('generate_', '').replace(/_/g, ' ') || 'MCP'} 生成
            </span>
          </div>
        </div>
      ) : (
        // G2模式：使用AntV G2渲染
        <div ref={containerRef} />
      )}
    </div>
  );
}
