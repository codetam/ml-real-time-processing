import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { VFileUpload } from 'vuetify/labs/VFileUpload'

export default createVuetify({
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          background:              '#0a0b0d',
          surface:                 '#111318',
          'surface-bright':        '#1a1d24',
          'surface-light':         '#1a1d24',
          'surface-variant':       '#1d2029',
          'on-background':         '#ffffff',
          'on-surface':            '#ffffff',
          'on-surface-variant':    '#8a919e',
          primary:                 '#0052ff',
          'primary-darken-1':      '#0042cc',
          secondary:               '#8a919e',
          'on-secondary':          '#ffffff',
          error:                   '#f56565',
          info:                    '#0052ff',
          success:                 '#05b169',
          warning:                 '#f59e0b',
        },
      },
    },
  },
  components: { VFileUpload },
})
